
import sys
import json
import base64
import subprocess
import threading

from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance


class AppleVisionOCR:
    def __init__(
        self,
        language="ja-JP",
        engine="visionkit",
        debug=False,
        debug_dir=None,
        try_rotations=False,
        reading_order="vision",
        language_correction=False,
        helper_path=None,
    ):
        if sys.platform != "darwin":
            raise RuntimeError("Apple OCR only works on macOS.")

        if engine not in ("vision", "visionkit", "auto"):
            raise ValueError("Invalid OCR engine.")

        if reading_order not in ("vision", "horizontal", "vertical"):
            raise ValueError("Invalid reading order.")

        self.language = language
        self.engine = engine
        self.debug = debug
        self.try_rotations = try_rotations
        self.reading_order = reading_order
        self.language_correction = language_correction

        self.debug_dir = Path(debug_dir) if debug_dir else None
        self.debug_count = 0

        self.helper_path = (
            Path(helper_path).expanduser().resolve()
            if helper_path
            else Path(__file__).resolve().parent / "visionkit_helper"
        )

        self.process = None
        self.lock = threading.RLock()

        if self.debug_dir:
            self.debug_dir.mkdir(parents=True, exist_ok=True)

        # only load the frameworks we need.
        if self.engine in ("vision", "auto"):
            import objc
            import Vision
            from Foundation import NSData

            self.objc = objc
            self.Vision = Vision
            self.NSData = NSData

            with objc.autorelease_pool():
                request = self.create_request()
                languages, error = request.supportedRecognitionLanguagesAndReturnError_(None)

                if error is not None:
                    raise RuntimeError(str(error))

                if self.language not in (languages or []):
                    raise RuntimeError(f"Unsupported language: {self.language}")

        if self.engine in ("visionkit", "auto"):
            self.start_visionkit()

    # create a normal Apple Vision OCR request
    def create_request(self):
        request = self.Vision.VNRecognizeTextRequest.alloc().init()

        request.setRecognitionLevel_(
            self.Vision.VNRequestTextRecognitionLevelAccurate
        )

        request.setRecognitionLanguages_([self.language])
        request.setAutomaticallyDetectsLanguage_(False)
        request.setUsesLanguageCorrection_(self.language_correction)
        request.setMinimumTextHeight_(0.0)

        return request

    # enlarge small images and add padding
    def prepare_image(self, image):
        image = image.convert("RGB")

        shortest = min(image.size)
        longest = max(image.size)

        scale = min(4.0, max(1.0, 96 / shortest), 2000 / longest)

        if scale > 1:
            width = round(image.width * scale)
            height = round(image.height * scale)

            image = image.resize(
                (width, height),
                Image.Resampling.LANCZOS
            )

        image = ImageOps.expand(image, border=16, fill="white")
        return image

    # convert a PIL image to PNG bytes
    def image_to_bytes(self, image):
        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()

    # recognize using the original Apple Vision API
    def recognize_vision_image(self, image):
        image_bytes = self.image_to_bytes(image)

        with self.objc.autorelease_pool():
            request = self.create_request()

            data = self.NSData.dataWithBytes_length_(
                image_bytes, len(image_bytes)
            )

            handler = self.Vision.VNImageRequestHandler.alloc().initWithData_options_(
                data, None
            )

            success, error = handler.performRequests_error_([request], None)

            if not success or error is not None:
                raise RuntimeError(f"Vision OCR failed: {error}")

            observations = list(request.results() or [])

            if self.reading_order == "horizontal":
                observations.sort(
                    key=lambda obs: (
                        -obs.boundingBox().origin.y,
                        obs.boundingBox().origin.x
                    )
                )

            elif self.reading_order == "vertical":
                observations.sort(
                    key=lambda obs: (
                        -obs.boundingBox().origin.x,
                        -obs.boundingBox().origin.y
                    )
                )

            texts = []

            for observation in observations:
                candidates = observation.topCandidates_(1)

                if candidates:
                    text = str(candidates[0].string()).strip()

                    if text:
                        texts.append(text)

            return "".join(texts)

    # try different preprocessing methods with Vision,
    # for some reason Vision works well with placed text 
    # next to eachother horizontally and not singular characters.
    # https://stackoverflow.com/questions/78644854/japanese-vertical-text-recognition-with-vnrecognizetextrequest-not-working
    def recognize_vision(self, image):
        prepared = self.prepare_image(image)

        # try the enlarged image first
        text = self.recognize_vision_image(prepared)
        if text:
            return text

        # try the original image
        text = self.recognize_vision_image(image)
        if text:
            return text

        # try grayscale with increased contrast
        gray = ImageOps.grayscale(prepared)
        gray = ImageOps.autocontrast(gray)
        gray = ImageEnhance.Contrast(gray).enhance(1.5)

        text = self.recognize_vision_image(gray)
        if text:
            return text

        # optionally try rotating vertical text as per the suggestion above
        if self.try_rotations and image.height > image.width * 1.5:
            for angle in (90, 270):
                rotated = prepared.rotate(angle, expand=True)

                text = self.recognize_vision_image(rotated)
                if text:
                    return text

        return ""

    # start the Swift VisionKit helper
    def start_visionkit(self):
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                return

            if not self.helper_path.is_file():
                raise FileNotFoundError(
                    f"VisionKit helper not found: {self.helper_path}"
                )

            self.process = subprocess.Popen(
                [str(self.helper_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )

            if self.debug:
                print("[VisionKit] Helper started")

    # recognize using VisionKit ImageAnalyzer
    def recognize_visionkit(self, image):
        image_bytes = self.image_to_bytes(image)

        payload = {
            "image": base64.b64encode(image_bytes).decode("ascii"),
            "language": self.language,
        }

        # only send one request at a time
        with self.lock:
            self.start_visionkit()

            try:
                self.process.stdin.write(json.dumps(payload) + "\n")
                self.process.stdin.flush()

                result = self.process.stdout.readline()

                if not result:
                    raise RuntimeError("VisionKit helper stopped responding.")

                response = json.loads(result)

            except (OSError, ValueError, RuntimeError) as error:
                self.close()
                raise RuntimeError(f"VisionKit failed: {error}") from error

        if response.get("error"):
            raise RuntimeError(response["error"])

        text = response.get("text", "").strip()

        # if self.debug:
        #     print(f"[VisionKit] {text}")

        return text

    # save images that OCR failed to recognize
    def save_failed_image(self, image):
        if self.debug_dir is None:
            return

        with self.lock:
            self.debug_count += 1
            path = self.debug_dir / f"failed_{self.debug_count:04d}.png"
            image.save(path)

        if self.debug:
            print(f"Saved failed image: {path}")

    # main OCR function.
    def __call__(self, image):
        if image.width <= 0 or image.height <= 0:
            raise ValueError("Image is empty.")

        # try VisionKit first
        if self.engine in ("visionkit", "auto"):
            text = self.recognize_visionkit(image)

            if text:
                return text

        # try normal Vision if requested
        if self.engine in ("vision", "auto"):
            text = self.recognize_vision(image)

            if text:
                return text

        self.save_failed_image(image)
        return ""

    # stop the Swift subprocess
    def close(self):
        with self.lock:
            if self.process is None:
                return

            process = self.process
            self.process = None

            if process.poll() is None:
                if process.stdin:
                    process.stdin.close()

                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.terminate()

                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()

            if process.stdout:
                process.stdout.close()

            if self.debug:
                print("[VisionKit] Helper stopped")
