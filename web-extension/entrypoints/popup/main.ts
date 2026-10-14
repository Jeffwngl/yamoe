import './style.css';
import { getOCRToken, getShowRegions, setOCRToken, setShowRegions } from '@/src/settings';
import { getFontSize, setFontSize } from '@/src/settings';

import {
    getDisplayMode,
    setDisplayMode,
    getCaptureMode,
    setCaptureMode,
    type OCRDisplayMode,
    type CaptureMode,
} from '@/src/settings';

document.querySelector<HTMLDivElement>('#app')!.innerHTML = `
  <div>
    <label>Backend token <input id="ocr-token" type="password" autocomplete="off"></label>
    <p>Copy the OCR token printed when the backend starts.</p>
    <label>
        OCR text size
        <input
            id="font-size"
            type="range"
            min="8"
            max="32"
            value="14"
        >
    </label>
    <label for="display-mode">
        Text style
    </label>

    <select id="display-mode">
        <option value="boxed">
            Black text / white background
        </option>

        <option value="outlined">
            White text / black outline
        </option>
    </select>

    <label class="checkbox-row">
        <span>Show detected regions:</span>
        <input type="checkbox" id="show-detected-regions" />
    </label>

    <label for="capture-mode">
        Capture mode
    </label>
    <select id="capture-mode">
        <option value="page">
            Whole page
        </option>

        <option value="textbox">
            Single text box
        </option>
    </select>

    <label for="help">
        Help
    </label>
    <div id="help">
        <p>Use Cmd/Crtl + shift + 1 to highlight text you want to process.</p>
        <p>Use Cmd/Crtl + shift + Q to delete all text.</p>
        <p>Use Cmd/Ctrl + shift + 3 to reselect previous region</p>
    </div>
  </div>
`;

// font size
const slider = document.querySelector<HTMLInputElement>('#font-size')!;

slider.value = String(await getFontSize());

slider.addEventListener('input', async () => {
    await setFontSize(Number(slider.value));
});

// display mode
const displaySelect = document.querySelector<HTMLSelectElement>('#display-mode')!;

displaySelect.value = await getDisplayMode();

displaySelect.addEventListener('change', async () => {
    await setDisplayMode(displaySelect.value as OCRDisplayMode);
});

// capture mode
const captureSelect = document.querySelector<HTMLSelectElement>('#capture-mode')!;

captureSelect.value = await getCaptureMode();

captureSelect.addEventListener('change', async () => {
    await setCaptureMode(captureSelect.value as CaptureMode);
});

const tokenInput = document.querySelector<HTMLInputElement>('#ocr-token')!;
tokenInput.value = await getOCRToken();
tokenInput.addEventListener('change', async () => {
    try {
        await setOCRToken(tokenInput.value);
    } catch (error) {
        console.error('Unable to save backend token:', error);
    }
});

// show detected regions
const showDetectedRegions = document.querySelector<HTMLInputElement>('#show-detected-regions')!;

showDetectedRegions.checked = await getShowRegions();
showDetectedRegions.addEventListener('change', async () => {
    await setShowRegions(showDetectedRegions.checked);
});
