import type { Point, Selection } from '@/lib/types';
import { BELOW_MAX_Z } from '@/lib/vals';
import { showPopupAnimated } from './ui';

type CaptureSelection = (selection: Selection) => void;
let stopActiveSelection: (() => void) | null = null;

export function cancelSelection() {
    stopActiveSelection?.();
}

let cachedSelection: Selection | null = null;

export function startSelection(captureSelection: CaptureSelection) {
    cancelSelection();
    const overlay = document.createElement('div');
    // showPopup('Press Esc to exit out of selection');
    showPopupAnimated('Press Esc to exit out of selection');

    Object.assign(overlay.style, {
        position: 'fixed',
        inset: '0',
        background: 'rgba(0, 0, 0, 0.25)',
        cursor: 'crosshair',
        touchAction: 'none',
        zIndex: BELOW_MAX_Z,
    });

    const selectionBox = document.createElement('div');

    Object.assign(selectionBox.style, {
        position: 'fixed',
        border: '1px solid white',
        pointerEvents: 'none',
        display: 'none',
    });

    overlay.appendChild(selectionBox);
    document.documentElement.appendChild(overlay);

    let start: Point | null = null;

    // handle stop selection
    const stopSelection = () => {
        //clearPopups();
        start = null;
        overlay.remove();
        document.removeEventListener('keydown', handleKeyDown);
        stopActiveSelection = null;
    };

    const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === 'Escape') {
            stopSelection();
        }
    };

    stopActiveSelection = stopSelection;
    document.addEventListener('keydown', handleKeyDown);

    overlay.addEventListener('pointerdown', (event) => {
        if (event.button !== 0) return;
        overlay.setPointerCapture(event.pointerId);
        start = {
            x: event.clientX,
            y: event.clientY,
        };

        selectionBox.style.display = 'block';
    });

    overlay.addEventListener('pointermove', (event) => {
        if (!start) {
            return;
        }

        const x = Math.min(start.x, event.clientX);
        const y = Math.min(start.y, event.clientY);

        const width = Math.abs(event.clientX - start.x);
        const height = Math.abs(event.clientY - start.y);

        Object.assign(selectionBox.style, {
            left: `${x}px`,
            top: `${y}px`,
            width: `${width}px`,
            height: `${height}px`,
        });
    });

    overlay.addEventListener('pointerup', (event) => {
        //clearPopups();
        if (!start) {
            return;
        }

        const selection: Selection = {
            x: Math.min(start.x, event.clientX),
            y: Math.min(start.y, event.clientY),
            width: Math.abs(event.clientX - start.x),
            height: Math.abs(event.clientY - start.y),
        };

        stopSelection();
        if (selection.width < 2 || selection.height < 2) {
            void showPopupAnimated('Select a larger region.');
            return;
        }
        cachedSelection = selection;

        captureSelection(selection);
    });
    overlay.addEventListener('pointercancel', stopSelection);
}

export function reselectSelection(captureSelection: CaptureSelection) {
    cancelSelection();
    if (cachedSelection === null) {
        void showPopupAnimated('No previously selected region.');
        return;
    }
    const x = Math.max(0, Math.min(cachedSelection.x, window.innerWidth));
    const y = Math.max(0, Math.min(cachedSelection.y, window.innerHeight));
    const width = Math.min(cachedSelection.width, window.innerWidth - x);
    const height = Math.min(cachedSelection.height, window.innerHeight - y);
    if (width < 4 || height < 4) {
        void showPopupAnimated('The previous region is outside this viewport. Select again.');
        return;
    }
    captureSelection({ x, y, width, height });
}

export async function cropScreenshot(
    screenshot: string,
    selection: Selection,
    viewportWidth: number,
    viewportHeight: number,
): Promise<Blob> {
    if (
        ![selection.x, selection.y, selection.width, selection.height, viewportWidth, viewportHeight].every(
            Number.isFinite,
        ) ||
        viewportWidth <= 0 ||
        viewportHeight <= 0 ||
        selection.width < 4 ||
        selection.height < 4 ||
        selection.x < 0 ||
        selection.y < 0 ||
        selection.x + selection.width > viewportWidth ||
        selection.y + selection.height > viewportHeight
    ) {
        throw new Error('Invalid selection. Select a region inside the viewport.');
    }
    const image = new Image();

    image.src = screenshot;

    await image.decode();

    const scaleX = image.naturalWidth / viewportWidth;
    const scaleY = image.naturalHeight / viewportHeight;

    const canvas = document.createElement('canvas');
    canvas.width = Math.round(selection.width * scaleX);
    canvas.height = Math.round(selection.height * scaleY);

    if (canvas.width * canvas.height > 16_000_000 || Math.max(canvas.width, canvas.height) > 8192) {
        throw new Error('Selected image is too large. Select a smaller region.');
    }
    const ctx = canvas.getContext('2d');

    if (!ctx) {
        throw new Error('Unable to get 2D canvas context');
    }

    ctx.drawImage(
        image,

        selection.x * scaleX,
        selection.y * scaleY,
        selection.width * scaleX,
        selection.height * scaleY,

        0,
        0,
        canvas.width,
        canvas.height,
    );

    return new Promise((resolve, reject) => {
        canvas.toBlob((blob) => {
            if (!blob) {
                reject(new Error('Failed to create crop'));

                return;
            }

            resolve(blob);
        }, 'image/png');
    });
}
