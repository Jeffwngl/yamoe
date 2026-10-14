
<div align="center">

# yamoe
*Yet Another Manga OCR Extension*

A **lightweight** browser-based OCR tool for converting manga images into selectable text.

Inspired by [Mokuro](https://github.com/kha-white/mokuro), [YomiNinja](https://github.com/matt-m-o/YomiNinja), and [Cloe](https://github.com/blueaxis/Cloe).

</div>


## About

A Manga OCR extension built on Apple Silicon, the extension leverages Apple's native Vision framework to reduce resource usage while remaining responsive.  

- Low memory usage: **~400 MB** (Apple Vision OCR) compared to **~1.8–2 GB** with MangaOCR.

- Fast OCR: ~2 seconds per manga page on an M4 MacBook Air.  

- Small download: **~225 MB** for the backend installation compared to **1-2 GB** normal Manga texte recognition OCR's.

For detailed performance comparisons, see the [Benchmarks](#performancebenchmarking) section.

## Background

*Yamoe* was developed to simplify my workflow for learning Japanese through manga, particularly the process of extracting text from images for Yomitan lookups.  

Existing tools like Mokuro and YomiNinja offer similar functionality, but don't quite fit my workflow. Mokuro focuses on local manga files, while YomiNinja provides a more general-purpose OCR solution with broader features and custom Yomichan integration.  

Yamoe instead focuses on lightweight, browser-native OCR, allowing users to select specific regions for text extraction and look up words directly with Yomitan, without continuous or whole-screen OCR. By favouring native OCR engines over heavier alternatives like MangaOCR, it aims to minimise memory usage and installation size.  

Development has primarily focused on macOS and Apple Silicon, reflecting my own setup and allowing the use of Apple's native Vision framework without CUDA. Windows support is also being developed, broader support is planned for the future.  

Currently, the default OCR engine for windows is Manga OCR, which is essentially the same functionality as other OCR apps, in this case, using another engine such as Cloe will give you similar results.

## Usage

Yamoe uses **on-demand OCR**, allowing you to extract text only when needed instead of continuously processing the page. Selected regions are cached for the current session, making it easy to perform OCR again as you read through manga pages.

### Getting Started

1. **Select a region:** Press `Ctrl/Cmd + Shift + 1`, then drag to select the area containing manga text.
2. **Extract text:** Wait for Yamoe to process the selected region. Recognised text will appear as selectable HTML overlays above the original image.
3. **Look up words:** Hover over the extracted text to use browser dictionaries such as [Yomitan](https://yomitan.wiki/).
4. **Reuse your selection:** Press `Ctrl/Cmd + Shift + 2` to perform OCR again on the previously selected region without having to drag a new selection.

![Yamoe Demo](public/demo.gif)

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl/Cmd + Shift + 1` | Select a new region for OCR |
| `Ctrl/Cmd + Shift + 2` | Reprocess the previously selected region |
| `Ctrl/Cmd + Shift + Q` | Clear existing OCR overlays |

### Example Workflow

| Select a Region | Extract Text |
|:---:|:---:|
| ![Select region](public/cropped1.png) | ![OCR processing](public/cropped2.png) |

Once processed, the recognised text is rendered as HTML elements directly over the manga image, enabling seamless integration with Yomitan and other browser-based dictionaries.

![Yomitan Integration](public/yomi.png)

### Tips

**Furigana recognition (macOS):** Apple Vision may occasionally include furigana alongside the main text, leading to inaccurate OCR results. If this happens, switch to **Text Box selection mode** and capture a smaller region to improve recognition.

**Reading multiple pages:** If the manga remains in the same position between pages, simply advance to the next page and press `Ctrl/Cmd + Shift + 2` to reuse your previous selection. No need to manually select the region again.

## Requirements

You will need:
- Python 3.10–3.12
- npm
- Chrome / Chromium or Firefox

## Known Issues

- Apple OCR sometimes detects furigana.
- Apple OCR doesnt detect big stylized fonts well.

## Pipeline

- The manga text extraction uses the following pipeline;
```
Screen Selected Image -> Comic Text Detector -> Manga OCR/Apple Vision OCR -> Displayed Text
```
- This project uses separate pipeline objects from Mokuro's singular Comic Text Detector to Manga OCR model/Apple Vision OCR, this is done to experiment and benchmark different OCR models.

## Install

- The backend prints a randomly generated OCR token at startup. Copy it into the **Backend token** field in the extension popup. By default the token changes whenever the backend restarts, including development reloads. Set the `YOMI_OCR_TOKEN` environment variable to a strong random value before starting the backend if you want the token to persist across restarts. Reload the extension after updating its permissions.

1. Clone the repo.
```
git clone https://github.com/Jeffwngl/yamoe.git
cd yamoe
```

1. Build and run backend.
- Note that on Windows, the application uses Manga OCR which contains and extra 400MB of model data which needs to be downloaded, as well as other large dependencies such as `pytorch`. I will try replace this with a alternative in the future such as `tesseract`.
```
cd ocr
build.sh
python -O backend.py
```
- You will find a OCR token as output, copy this to clipboard as this will be used later.
1. Build and run frontend.
```
cd ..
cd web-extension
npm install
npm run dev
```
1. Enter OCR token code in extension dropdown and use extension.

## Development
- Follow the same steps as the install, except;
- On chrome, go to extensions, load unpacked and load the chrome-mv3-dev folder.
- Also add the OCR Token to the extension.

## Performance/Benchmarking

| Metric | Apple Vision | MangaOCR |
|---|---:|---:|
| Physical Footprint | **399 MB** | 1,827 MB |
| Peak Physical Footprint | **399 MB** | 1,876 MB |
| IOAccelerator Memory | ~0 MB | 1,386 MB |
| Average Processing Time | **2.14 s** | 3.04 s |

**Note:** Memory benchmarks measured using macOS `footprint` on Apple Silicon.  
**Note:** Memory figures represent the Python backend process only. External OCR helper processes and system services are not included.  

- My requirements from this project was that it had to be lightweight (around 500MB of memory), small, meaning no large packages and models and performant to a degree meaning it cannot be too slow to ruin the reading experience. For speed, I decided that 3-4 secs was the upper limit to what I tolerate (I am a pretty slow reader), and for the size, I wanted the application to be small enough as well so I've also used a stripped down version of CTD so that unused areas are not imported, Smaller models were also used which means that it will be slightly faster to run and smaller in size but also means that it won't be as accurate, I have weighed the pros and cons of each optimization here to achieve something which is "good enough" to use day to day, while I would also like to add the choice to select larger and more heavy models and settings in the future.  
- My understanding of machine learning and OCR models is still relatively limited, so some of my explanations or assumptions regarding model behaviour and performance may not be entirely accurate. Corrections and suggestions are welcome.
- On a M4 macbook air, the main performance bottleneck lies in the detection using to extract characters out of the bounding boxes, an initial benchmark using the original model, on average, extracting bounding boxes take around 1.5s sec while extracting a single sentence takes around 0.1 sec, collectively for an average of 15 boxes per image for a page of manga, this adds up to be quite significant.
- As such, text detection can be coupled with different OCR models which will be added in a future update, so far, Apple's Vision framework provides OCR detection with hardware acceleration, provides some performance improvements, a method for windows is still in the works.   
- The majority of the optimization is focused on Comic Text Detector.

### CTD + MangaOCR Performance
- The pipeline requires running two fairly large ML models locally and is currently what users on windows will use, Comic Text Detector is used for detecting the bounding boxes of the text in a page and Manga OCR is used to extract the text in the bounding boxes.
- Tweaking the input size parameter on the CTD model can be managed in `detector.py` (credit to [Comic Text Detector](https://github.com/dmMaze/comic-text-detector)). The original `onnx` file model uses a fixed input size of 1024, which produces the baseline performance shown above.
- To retain the performance benefits of ONNX while experimenting with different input resolutions, additional ONNX models with fixed input sizes of 768 and 640 are used.

Machine: Apple M4 (average across 6 pages)
| Input Size | CTD time | MangaOCR time | Blocks |
| --- | --- | --- | --- |
| 1024 | 1.497s | 0.902s | 9.67 |
| 768 | 0.787s | 0.930s | 9.33 |
| 640 | 0.543s | 0.929s | 9.5 |

- I have found the 768 model currently provides the best overall balance between detection accuracy and performance. It produced results very similar to the original 1024 model while reducing CTD inference time from approximately 1.50 s to 0.79 s.
- The 640 model is faster again, reducing CTD inference time to approximately 0.54 s, and still performs well on many pages. However, its reliability is more dependent on page layout, text size, and image quality, with smaller or more difficult text regions being more likely to be missed.
- Interestingly, changing the CTD input resolution has very little effect on MangaOCR inference time. This is expected because the input size primarily affects the text-detection stage; MangaOCR still processes the resulting cropped text regions independently.
- For day-to-day use, 768 is the recommended default, while 640 is useful when prioritising speed and 1024 can be used when maximum detection reliability is preferred.

| CTD Input Size 768 | CTD Input Size 640 |
:-------------------------:|:-------------------------:
![768](/public/768.png) | ![640](/public/640.png)

- RAM usage is another consideration taken into account, the model weights are and tensors are loaded into memory on startup of the backend, these can be considerable when added up.
- The application loads the model and model weights onto RAM, regular RAM usage for this application oscillates around 200-700MB.
- The application remains around 500MB when idle, 200MB on startup and around 700-750MB after processing a full screen image.

- Using the torchless version of Manga OCR with the original model using CPU inference takes around 2.5 s per page
- The size of Manga-OCR with torch is approximately 951MB while the torchless version is around 452MB, however, this is extremely slow for regions of long text without KV caching and GPU acceleration so I think it is necessary to keep the original version for now. In the future, I will look into exporting a version with KV caching if I am able to.

### CTD + Apple Vision OCR Performance
- Benchmarks comparing Apple Vision and MangaOCR using Comic Text Detector (CTD) for text region detection. All timings are in seconds.

| Metric | Apple Vision | MangaOCR |
|---|---:|---:|
| CTD Detection (avg) | 0.7704 | 0.7758 |
| OCR Processing (avg) | 1.3718 | 2.2640 |
| Text Blocks (avg) | 38.8 | 39.0 |
| **Total Time (avg)** | **2.1422** | **3.0398** |

## Development Updates/Ramblings
- Currently, the install size is relatively large due to Manga OCR and Pytorch, Manga OCR needs pytorch in order to run the model, however, there are methods to run it torchless, the Manga OCR `onnx` model is around 400MB which is unavoidable unless another OCR model is chosen but we can decrease the install size which saves around 2GB.
- I have considered using a (quantized version of Manga OCR)[https://huggingface.co/kimchireader/manga-ocr-onnx-q8], however, seeing that it only decreases the size of the model by around 200-300MB, I decided that It doesn't really affect the outcome so I will keep the original model.
- I've added a trial run with Manga-OCR torchless, while it doesn't require torch or any large packages anymore significantly decreasing the install size, the time it takes for Manga OCR shot up from around 1 s to around 2.5 s through CPU inference with `force_cpu=True`, however, with `force_cpu=False`, the time taken is around 6 s, I might add this back later.
- Manga OCR torchless doesn't implement KV caching which significantly increases inference time specifically when there are long regions of text, this is because the exported model doesn't expose a mechanism for KV caching.
- Smaller OCR models also offer the advantage of reduced memory consumption, as fewer model weights need to be loaded into RAM which is why I wanted to look for alternatives to Manga OCR in the first place.
- Initially tested Apple Vision OCR as a lightweight alternative to MangaOCR. Early results were unreliable, particularly with vertical Japanese text, where it frequently failed to recognise text in otherwise clear regions.
- After further improvements to the Apple Vision pipeline and its integration with Comic Text Detector (CTD), recognition accuracy has improved substantially. Apple Vision now achieves faster OCR processing and significantly lower memory usage than the original MangaOCR implementation, making it the preferred engine on macOS.

## Future Updates

- I would like to add the ability to tweak the text extraction OCR in the future, so far, it just uses Manga OCR's fixed settings, I will also add the ability to choose between using Apple's Vision OCR as well.
- I've heard that adding batch processing instead of individual passes is much better for ML models, I'll add this in a future update for text extraction.
- So far, the only model I've found on windows which suits this project is Tesseract OCR, I'll try add this as well later.

## OCR Tools
Manga OCR - [manga ocr](https://github.com/kha-white/manga-ocr)  
Comic Text Detector - [comic text detector](https://github.com/zyddnys/manga-image-translator/releases/tag/beta-0.3)  
Manga OCR torchless - [manga ocr torchless](https://github.com/liksunrice/manga-ocr-torchless)
Apple Visionkit - [apple visionkit](https://developer.apple.com/documentation/visionkit)