import { defineConfig } from 'wxt';

// See https://wxt.dev/api/config.html
export default defineConfig({
    manifest: {
        name: 'Yomi Web',
        description: 'An OCR tool to extract text from webpages.',
        permissions: ['activeTab', 'storage', 'notifications'],
        host_permissions: ['http://127.0.0.1:8000/*'],
        commands: {
            'start-ocr': {
                suggested_key: {
                    default: 'Ctrl+Shift+1',
                    mac: 'Command+Shift+1',
                },
                description: 'Start OCR selection',
            },
            'clear-ocr': {
                suggested_key: {
                    default: 'Ctrl+Shift+Q',
                    mac: 'Command+Shift+Q',
                },
                description: 'Clear OCR overlays',
            },
            'reselect-region': {
                suggested_key: {
                    default: 'Ctrl+Shift+2',
                    mac: 'Command+Shift+2',
                },
                description: 'Reselect previously selected region',
            },
        },
    },
});
