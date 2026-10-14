import { startSelection, cropScreenshot, reselectSelection, cancelSelection } from '@/src/selection';
import { showDetectedRegions, showOCRRegions, clearOCRRegions, showPopupAnimated } from '@/src/ui';
import { sendToOCR, cancelOCR } from '@/src/client';
import { getCaptureMode, getShowRegions } from '@/src/settings';
import type { Selection } from '@/lib/types';

export default defineContentScript({
    matches: ['<all_urls>'],

    main(ctx) {
        let requestId: string | null = null;

        function invalidate() {
            if (requestId) {
                cancelOCR(requestId);
            }
            requestId = null;
            cancelSelection();
            clearOCRRegions(false);
        }

        ctx.addEventListener(window, 'scroll', invalidate, { capture: true, passive: true });
        ctx.addEventListener(window, 'resize', invalidate);
        ctx.addEventListener(window, 'pagehide', invalidate);
        ctx.addEventListener(document, 'visibilitychange', () => {
            if (document.hidden) invalidate();
        });
        ctx.addEventListener(window, 'keydown', (event) => {
            if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
                invalidate();
            }
        });
        ctx.onInvalidated(invalidate);

        async function captureSelection(selection: Selection) {
            invalidate();
            const id = crypto.randomUUID();
            requestId = id;
            const viewport = { width: window.innerWidth, height: window.innerHeight };
            void showPopupAnimated('Analyzing page...');
            try {
                // allow the removed selection overlay to leave the rendered screenshot.
                await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));

                if (requestId !== id) {
                    return;
                }

                const capture = await browser.runtime.sendMessage({ type: 'CAPTURE_SELECTION' });

                if (requestId !== id) {
                    return;
                }

                if (!capture?.ok) {
                    throw new Error(capture?.error || 'Screenshot capture failed.');
                }

                const blob = await cropScreenshot(capture.screenshot, selection, viewport.width, viewport.height);

                const captureMode = await getCaptureMode();
                if (requestId !== id) {
                    return;
                }

                const result = await sendToOCR(blob, captureMode, id);

                if (requestId !== id) return;

                if (!result.valid) {
                    void showPopupAnimated(result.reason || 'No text found.');
                    return;
                }

                // settings reads are asynchronous, so rendering checks the operation again.
                const showRegions = await getShowRegions();
                await showOCRRegions(result.regions, selection, () => requestId === id);

                if (requestId === id && showRegions) {
                    showDetectedRegions(result.regions, selection);
                }
            } catch (error) {
                if (requestId === id) {
                    console.error('[content] OCR failed:', error);
                    void showPopupAnimated(error instanceof Error ? error.message : 'OCR failed.', 5000);
                }
            }
        }

        browser.runtime.onMessage.addListener((message) => {
            if (message.type === 'START_SELECTION') {
                invalidate();

                startSelection((selection) => {
                    void captureSelection(selection);
                });
            } else if (message.type === 'RESELECT_REGION') {
                invalidate();

                reselectSelection((selection) => {
                    void captureSelection(selection);
                });
            } else if (message.type === 'CLEAR_OCR') {
                invalidate();

                void showPopupAnimated('Cleared page.');
            }
        });
    },
});
