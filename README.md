# yamoe
*Yet Another Manga OCR Extension*  

A **lightweight** web OCR tool to convert images to text, inspired by [Mokuro](https://github.com/kha-white/mokuro), [YomiNinja](https://github.com/matt-m-o/YomiNinja) and [Cloe](https://github.com/blueaxis/Cloe).

## About

This project is a tool I developed around my own workflow for learning Japanese through manga. I primarily use Yomitan to look up unfamiliar words, build vocabulary, and support reading comprehension, one thing that I have found tedious when reading japanese manga specifically is the whole workflow of image to OCR to translation.

I considered several existing tools, including Mokuro and YomiNinja. Both solve similar problems well, but neither quite fit how I read manga. Mokuro relies on local files, where I primarily read directly from websites like SJP. YomiNinja covers most of what I need and offers more features, including multiple OCR engines, but it's designed more for general purpose OCR, with features like whole-screen extraction and requiring custom Yomichan integration.  

Yomi Web instead focuses on a lighter, browser based workflow, allowing users to select and extract only the regions they need without processing the entire screen or using auto OCR. Since it runs directly in the browser, tools like Yomitan integrate seamlessly. It doesn't use heavy OCR engines such as Manga OCR but instead focuses on lighter alternatives to keep RAM usage and download size small.  

I mainly use this tool locally on my MacBook Air, so development has so far been focused around macOS and the Apple ecosystem, i.e. no NVIDIA CUDA acceleration. Some implementation decisions and platform-specific features may currently favour macOS, but the plan is to broaden the scope to windows and linux too.  

Currently, on a M4 macbook air, it achieves around 3 s per two pages, has a download size of ... and uses around ... of RAM.

- NOTE THAT THIS PROJECT IS CURRENTLY STILL IN DEVELOPMENT.

## Usage

- The text sits on a overlay layer above the webpage as html elements, you can easily use dictionaries such as [Yomitan](https://yomitan.wiki/) to look up words.
- Yomi Web extracts text as DOM elements on the page, Yomitan and other browser dictionaries should be able to integrate seamlessly with it.

![demo](public/demo.gif)

Ctrl/Cmd + Shift + 1       |  Select region
:-------------------------:|:-------------------------:
![select](/public/cropped1.png)  |  ![process](/public/cropped2.png)
- Then wait for the OCR to process the image.
- `Ctrl/Cmd + Shift + Q` erases the processed texts.
- `Ctrl/Cmd + Shift + 2` recaptures the previously captured region.
- From here you can use Yomitan or other tools you have;

![yomi](/public/yomi.png)

- On MacOS, it sometimes may capture the Furigana on the page and cause some incorrect text to appear, you can recapture the text using the text box selection mode to get a better translation.

## Requirements

You will need:
- Python 3.10–3.12
- npm
- Chrome / Chromium or Firefox

## Pipeline

- The manga text extraction uses the following pipeline;
```
Screen Selected Image -> Comic Text Detector -> Manga OCR/Apple Vision OCR -> Displayed Text
```
- This project uses separate pipeline objects from Mokuro's singular Comic Text Detector to Manga OCR model/Apple Vision OCR, this is done to experiment and benchmark different OCR models.
- 
## Install

- Three different types of models can be installed depending on the input size of the CTD OCR, for day-to-day use, the 768 model is recommended and is what this application comes with my default, see benchmarking below for more details.
- To change the model input size, drag the desired model into your backend files under models and update the `detector.py` input size and model path parameters.

- The backend prints a randomly generated OCR token at startup. Copy it into the **Backend token** field in the extension popup. By default the token changes whenever the backend restarts, including development reloads. Set the `YOMI_OCR_TOKEN` environment variable to a strong random value before starting the backend if you want the token to persist across restarts. Reload the extension after updating its permissions.

1. Clone the repo.
```
git clone https://github.com/Jeffwngl/yamoe.git
cd yamoe
```

2. Build and run backend.
- Note that on Windows, the application uses Manga OCR which contains and extra 400MB of model data which needs to be downloaded, as well as other large dependencies such as `pytorch`. I will try replace this with a alternative in the future such as `tesseract`.
```
cd ocr
build.sh
python -O backend.py
```
- You will find a OCR token as output, copy this to clipboard as this will be used later.
3. Build and run frontend.
```
cd ..
cd web-extension
npm install
npm run dev
```
4. Enter OCR token code in extension dropdown and use extension.

## Development
- Follow the same steps as the install, except;
- On chrome, go to extensions, load unpacked and load the chrome-mv3-dev folder.
- Also add the OCR Token to the extension.

## Performance/Benchmarking
- My requirements from this project was that it had to be lightweight (around 500MB of memory), small, meaning no large packages and models and performant to a degree meaning it cannot be too slow to ruin the reading experience. For speed, I decided that 3-4 secs was the upper limit to what I tolerate (I am a pretty slow reader), and for the size, I wanted the application to be small enough as well so I've also used a stripped down version of CTD so that unused areas are not imported, Smaller models were also used which means that it will be slightly faster to run and smaller in size but also means that it won't be as accurate, I have weighed the pros and cons of each optimization here to achieve something which is "good enough" to use day to day, while I would also like to add the choice to select larger and more heavy models and settings in the future.  
- My understanding of machine learning and OCR models is still relatively limited, so some of my explanations or assumptions regarding model behaviour and performance may not be entirely accurate. Corrections and suggestions are welcome.
- On a M4 macbook air, the main performance bottleneck lies in the detection using to extract characters out of the bounding boxes, an initial benchmark using the original model, on average, extracting bounding boxes take around 1.5s sec while extracting a single sentence takes around 0.1 sec, collectively for an average of 15 boxes per image for a page of manga, this adds up to be quite significant.
- As such, text detection can be coupled with different OCR models which will be added in a future update, so far, Apple's Vision framework provides OCR detection with hardware acceleration, provides some performance improvements, a method for windows is still in the works.   
- The majority of the optimization is focused on Comic Text Detector.

### CTD + MangaOCR Performance
- The pipeline requires running two fairly large ML models locally and is currently what users on windows will use, Comic Text Detector is used for detecting the bounding boxes of the text in a page and Manga OCR is used to extract the text in the bounding boxes.
- Tweaking the input size parameter on the CTD model can be managed in `detector.py` (credit to [Comic Text Detector](https://github.com/dmMaze/comic-text-detector)). The original `onnx` file model uses a fixed input size of 1024, which produces the baseline performance shown above.
- The `pytorch` model allows tweaking input size parameters but doesn't provide more reliable performance enhancements compared to the `onnx` version due to the pytorch runtime overhead.
- To retain the performance benefits of ONNX while experimenting with different input resolutions, I also exported additional ONNX models with fixed input sizes of 768 and 640.

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

- This is the version is supported by apple devices due to the Apple vision OCR library.

## Development Updates
- Currently, the install size is relatively large due to Manga OCR and Pytorch, Manga OCR needs pytorch in order to run the model, however, there are methods to run it torchless, the Manga OCR `onnx` model is around 400MB which is unavoidable unless another OCR model is chosen but we can decrease the install size which saves around 2GB.
- I have considered using a (quantized version of Manga OCR)[https://huggingface.co/kimchireader/manga-ocr-onnx-q8], however, seeing that it only decreases the size of the model by around 200-300MB, I decided that It doesn't really affect the outcome so I will keep the original model.
- I've added a trial run with Manga-OCR torchless, while it doesn't require torch or any large packages anymore significantly decreasing the install size, the time it takes for Manga OCR shot up from around 1 s to around 2.5 s through CPU inference with `force_cpu=True`, however, with `force_cpu=False`, the time taken is around 6 s, I might add this back so I can use it on my other laptop with no GPU.
- Manga OCR torchless doesn't implement KV caching which significantly increases inference time specifically when there are long regions of text, this is because the exported model doesn't expose a mechanism for KV caching.
- Another benefit of smaller models also will have a smaller amount of weights needed to be uploaded into RAM.
- I ran some tests with apple vision ocr, it doesn't seem to work well on vertical and manga text failing to detect text in regions where there is obviously text, I am still looking into a fast and small alternative to Manga OCR.
- I have gotten Apple Vision OCR to work well now with CTD, the speeds are much faster compared to OCR and the RAM usage is also much lower.

## Future Updates

- I would like to add the ability to tweak the text extraction OCR in the future, so far, it just uses Manga OCRS's fixed settings, I will also add the ability to choose between using Apple's Vision OCR as well.
- I've heard that adding batch processing instead of individual passes is much better for ML models, I'll add this in a future update for text extraction.
- So far, the only model I've found on windows which suits this project is Tesseract OCR, I'll try add this as well later.

## OCR Tools
Manga OCR - [manga ocr](https://github.com/kha-white/manga-ocr)  
Comic Text Detector - [comic text detector](https://github.com/zyddnys/manga-image-translator/releases/tag/beta-0.3)  
https://github.com/zyddnys/manga-image-translator/releases/tag/beta-0.3
Manga OCR torchless - [manga ocr torchless](https://github.com/liksunrice/manga-ocr-torchless)