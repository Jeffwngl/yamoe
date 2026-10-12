import asyncio
import logging
import os
import secrets
import threading
import warnings
from contextlib import asynccontextmanager
from io import BytesIO
from typing import Annotated

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from pipeline import CaptureMode, detect_regions

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
MAX_IMAGE_SIDE = 8192
MAX_TEXTBOX_SIDE = 1200

OCR_TOKEN = os.environ.get("YOMI_OCR_TOKEN") or secrets.token_urlsafe(32)
logger = logging.getLogger("uvicorn.error")

# only accept one OCR request at a time
request_lock = asyncio.Lock()

# protect the shared model if a request is canceled during inference
model_lock = threading.Lock()

@asynccontextmanager
async def lifespan(app):
    # uvicorn has configured logging by the time the server starts
    logger.info("Yomi Web OCR token: %s", OCR_TOKEN)
    yield

app = FastAPI(lifespan=lifespan)

async def read_request_body(receive):
    body = bytearray()

    while True:
        message = await receive()

        if message["type"] == "http.disconnect":
            return None

        body.extend(message.get("body", b""))

        if len(body) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Upload exceeds 10 MiB.")

        if not message.get("more_body", False):
            return bytes(body)

class OCRRequestMiddleware:
    # check authentication and size before FastAPI parses the uploaded file
    # scope contains request information; receive/send read and write messages
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] != "/ocr":
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        token = headers.get(b"authorization", b"")
        expected_token = ("Bearer " + OCR_TOKEN).encode("utf-8")

        try:
            if not secrets.compare_digest(token, expected_token):
                raise HTTPException(401, "Invalid OCR token.")

            body = await read_request_body(receive)
        except HTTPException as error:
            response = JSONResponse(
                {"detail": error.detail},
                status_code=error.status_code
            )
            await response(scope, receive, send)
            return

        if body == None:
            return

        # FastAPI still needs to receive the body that we already checked
        body_delivered = False

        async def receive_body():
            nonlocal body_delivered

            if body_delivered:
                return await receive()

            body_delivered = True

            return {
                "type": "http.request",
                "body": body,
                "more_body": False
            }

        await self.app(scope, receive_body, send)

app.add_middleware(OCRRequestMiddleware)

def open_image(data, capture_mode):
    try:
        # treat Pillows oversized image warnings as errors.
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)

            with Image.open(BytesIO(data)) as image:
                width, height = image.size
                pixels = width * height
                longest_side = max(width, height)

                if pixels > MAX_IMAGE_PIXELS or longest_side > MAX_IMAGE_SIDE:
                    raise HTTPException(413, "Image dimensions are too large.")

                if capture_mode == CaptureMode.TEXTBOX and longest_side > MAX_TEXTBOX_SIDE:
                    raise HTTPException(413, "Textbox dimensions must not exceed 1200 pixels.")

                return image.convert("RGB")

    except (Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise HTTPException(413, "Image dimensions are too large.") from error

    except (UnidentifiedImageError, OSError, SyntaxError) as error:
        raise HTTPException(400, "Invalid or unsupported image.") from error


def process_image(data, capture_mode):
    with open_image(data, capture_mode) as image:
        with model_lock:
            return detect_regions(image, capture_mode)

@app.post("/ocr")
async def ocr(image: Annotated[UploadFile, File()], captureMode: Annotated[CaptureMode, Form()]):
    try:
        if request_lock.locked():
            raise HTTPException(429, "OCR is busy. Try again shortly.")

        async with request_lock:
            data = await image.read(MAX_UPLOAD_BYTES + 1)

            if len(data) > MAX_UPLOAD_BYTES:
                raise HTTPException(413, "Upload exceeds 10 MiB.")

            # keep image processing off the server's async event loop
            result = await run_in_threadpool(process_image, data, captureMode)
            return result

    except HTTPException:
        raise

    except Exception as error:
        logger.exception("OCR processing failed")
        raise HTTPException(
            500,
            "OCR processing failed. Check the backend logs."
        ) from error

    finally:
        await image.close()
