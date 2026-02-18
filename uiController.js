import {
    convertAudioOnline,
    convertLibreOfficeOnline,
    deleteStoredDocument,
    downloadDocumentConversionJob,
    downloadStoredDocument,
    getAudioFormats,
    getDocumentConversionJobStatus,
    getDocumentDebug,
    getDocumentFormats,
    getDocumentOptions,
    getLibreOfficeFormats,
    listStoredDocuments,
    startDocumentConversionJob,
    storeDocument,
    triggerDownload
} from './browserApi.js';

function getElements() {
    return {
        docFile: document.getElementById('doc-file'),
        docType: document.getElementById('doc-type'),
        docOutputProfile: document.getElementById('doc-output-profile'),
        docOutputFormat: document.getElementById('doc-output-format'),
        docDebug: document.getElementById('doc-debug'),
        docDebugOutput: document.getElementById('doc-debug-output'),
        docConvertBtn: document.getElementById('doc-convert-btn'),
        docProgressText: document.getElementById('doc-progress-text'),
        docUploadBar: document.getElementById('doc-upload-bar'),
        docProgressBar: document.getElementById('doc-progress-bar'),
        docSelectedFile: document.getElementById('doc-selected-file'),
        docUploadSpeed: document.getElementById('doc-upload-speed'),
        docElapsedTime: document.getElementById('doc-elapsed-time'),
        docEtaTime: document.getElementById('doc-eta-time'),
        docStatusArea: document.getElementById('doc-status-area'),
        loFile: document.getElementById('lo-file'),
        loOutputFormat: document.getElementById('lo-output-format'),
        loConvertBtn: document.getElementById('lo-convert-btn'),
        loStatusArea: document.getElementById('lo-status-area'),
        audioFile: document.getElementById('audio-file'),
        audioOutputFormat: document.getElementById('audio-output-format'),
        audioBitrate: document.getElementById('audio-bitrate'),
        audioConvertBtn: document.getElementById('audio-convert-btn'),
        audioStatusArea: document.getElementById('audio-status-area'),
        calcRoot: document.getElementById('calc-root'),
        calcStatusArea: document.getElementById('calc-status-area'),
        storeDocFile: document.getElementById('store-doc-file'),
        storeDocName: document.getElementById('store-doc-name'),
        storedDocList: document.getElementById('stored-doc-list'),
        storeDocBtn: document.getElementById('store-doc-btn'),
        refreshDocListBtn: document.getElementById('refresh-doc-list-btn'),
        downloadDocBtn: document.getElementById('download-doc-btn'),
        deleteDocBtn: document.getElementById('delete-doc-btn'),
        docLibraryStatusArea: document.getElementById('doc-library-status-area')
    };
}

function setStatus(element, message, type = 'ok') {
    if (!element) {
        return;
    }
    element.textContent = message;
    element.dataset.status = type;
}

function setDebugOutput(els, payload) {
    if (!els.docDebugOutput) {
        return;
    }

    if (!payload) {
        els.docDebugOutput.textContent = '';
        els.docDebugOutput.style.display = 'none';
        return;
    }

    els.docDebugOutput.style.display = 'block';
    els.docDebugOutput.textContent = JSON.stringify(payload, null, 2);
}

function setDocumentProgress(els, value, text = '') {
    const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
    if (els.docProgressBar) {
        els.docProgressBar.style.width = `${safeValue}%`;
    }
    if (els.docProgressText) {
        els.docProgressText.textContent = text || `Progress: ${safeValue}%`;
    }
}

function setUploadProgress(els, value) {
    const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
    if (els.docUploadBar) {
        els.docUploadBar.style.width = `${safeValue}%`;
    }
}

function formatBytesPerSecond(value) {
    if (!Number.isFinite(value) || value <= 0) {
        return '0 KB/s';
    }
    if (value < 1024) {
        return `${value.toFixed(0)} B/s`;
    }
    if (value < 1024 * 1024) {
        return `${(value / 1024).toFixed(1)} KB/s`;
    }
    return `${(value / (1024 * 1024)).toFixed(2)} MB/s`;
}

function formatDurationMs(ms) {
    if (!Number.isFinite(ms) || ms <= 0) {
        return '0s';
    }
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    if (minutes > 0) {
        return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function initCalculator(els) {
    if (!els.calcRoot) {
        return;
    }

    const shell = document.createElement('div');
    shell.style.maxWidth = '360px';
    shell.style.border = '1px solid #d1d5db';
    shell.style.borderRadius = '10px';
    shell.style.padding = '10px';
    shell.style.background = '#f9fafb';

    const display = document.createElement('input');
    display.type = 'text';
    display.readOnly = true;
    display.value = '0';
    display.style.width = '100%';
    display.style.marginBottom = '10px';
    display.style.padding = '10px';
    display.style.fontSize = '1.15rem';
    display.style.textAlign = 'right';
    display.style.border = '1px solid #cbd5e1';
    display.style.borderRadius = '8px';

    const keypad = document.createElement('div');
    keypad.style.display = 'grid';
    keypad.style.gridTemplateColumns = 'repeat(4, minmax(0, 1fr))';
    keypad.style.gap = '8px';

    const keys = ['7', '8', '9', '/', '4', '5', '6', '*', '1', '2', '3', '-', '0', '.', 'C', '+', 'DEL', '='];
    let expression = '';

    const updateDisplay = () => {
        display.value = expression || '0';
    };

    const evalExpression = () => {
        if (!expression) {
            setStatus(els.calcStatusArea, 'Enter an expression first.', 'error');
            return;
        }
        try {
            // Restrict to calculator-safe characters before evaluating.
            if (!/^[0-9+\-*/.()\s]+$/.test(expression)) {
                throw new Error('Invalid expression');
            }
            const value = Function(`"use strict"; return (${expression})`)();
            if (!Number.isFinite(value)) {
                throw new Error('Invalid calculation');
            }
            expression = String(value);
            updateDisplay();
            setStatus(els.calcStatusArea, 'Calculation complete.', 'ok');
        } catch (_error) {
            expression = '';
            updateDisplay();
            setStatus(els.calcStatusArea, 'Invalid expression.', 'error');
        }
    };

    keys.forEach((key) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = key === '=' ? 'action-btn primary' : 'action-btn';
        button.textContent = key;
        button.addEventListener('click', () => {
            if (key === 'C') {
                expression = '';
                updateDisplay();
                setStatus(els.calcStatusArea, 'Calculator cleared.', 'ok');
                return;
            }
            if (key === 'DEL') {
                expression = expression.slice(0, -1);
                updateDisplay();
                return;
            }
            if (key === '=') {
                evalExpression();
                return;
            }
            expression += key;
            updateDisplay();
        });
        keypad.appendChild(button);
    });

    shell.appendChild(display);
    shell.appendChild(keypad);
    els.calcRoot.innerHTML = '';
    els.calcRoot.appendChild(shell);
}

function initNavigation() {
    const links = [...document.querySelectorAll('.sidebar-nav a[href^="#"]')];
    const sections = links
        .map((link) => document.querySelector(link.getAttribute('href')))
        .filter((section) => section);

    const showOnly = (activeLink) => {
        const target = document.querySelector(activeLink.getAttribute('href'));
        if (!target) {
            return;
        }

        sections.forEach((section) => {
            section.style.display = section === target ? '' : 'none';
        });

        links.forEach((item) => {
            const parent = item.closest('li');
            if (parent) {
                parent.classList.toggle('active', item === activeLink);
            }
        });
    };

    links.forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            showOnly(link);
        });
    });

    if (links.length > 0) {
        showOnly(links[0]);
    }
}

function normalizeFormats(list) {
    return (list || []).map((ext) => ext.replace(/^\./, '').toLowerCase());
}

function populateSelect(select, values, currentValue = '') {
    select.innerHTML = '';
    values.forEach((value) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value.toUpperCase();
        select.appendChild(option);
    });

    if (currentValue && values.includes(currentValue)) {
        select.value = currentValue;
    }
}

function getEffectiveType(els, docOptions) {
    if (els.docType.value !== 'auto') {
        return els.docType.value;
    }
    return docOptions.defaultType || 'text';
}

function refreshOutputFormats(els, docOptions) {
    const effectiveType = getEffectiveType(els, docOptions);
    const profile = els.docOutputProfile.value;
    const current = els.docOutputFormat.value;

    const byType = docOptions.outputsByTypeAndProfile?.[effectiveType] || {};
    const formats = normalizeFormats(byType[profile]);

    if (formats.length === 0) {
        populateSelect(els.docOutputFormat, ['pdf'], current);
        return;
    }

    populateSelect(els.docOutputFormat, formats, current);
}

async function loadDocumentControls(els) {
    const [formats, options] = await Promise.all([getDocumentFormats(), getDocumentOptions()]);

    const typeValues = ['auto', ...(options.types || [])];
    els.docType.innerHTML = '';
    typeValues.forEach((value) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value === 'auto' ? 'AUTO (detect from file)' : value.toUpperCase();
        els.docType.appendChild(option);
    });

    const profileValues = options.profiles || ['legacy', 'modern'];
    populateSelect(els.docOutputProfile, profileValues, options.defaultProfile || 'modern');

    const fallbackOutputs = normalizeFormats(formats.output);
    if (!options.outputsByTypeAndProfile) {
        populateSelect(els.docOutputFormat, fallbackOutputs, 'pdf');
        return {
            defaultType: 'text',
            defaultProfile: 'modern',
            outputsByTypeAndProfile: {
                text: {
                    modern: fallbackOutputs
                }
            }
        };
    }

    refreshOutputFormats(els, options);
    return options;
}

async function convertDocument(els, docOptions) {
    const file = els.docFile.files?.[0];
    if (!file) {
        setStatus(els.docStatusArea, 'Select a source file before converting.', 'error');
        return;
    }

    const outputFormat = els.docOutputFormat.value;
    if (!outputFormat) {
        setStatus(els.docStatusArea, 'Choose an output format.', 'error');
        return;
    }

    const documentType = els.docType.value || 'auto';
    const outputProfile = els.docOutputProfile.value || (docOptions.defaultProfile || 'modern');
    const debug = Boolean(els.docDebug?.checked);
    const startedAt = Date.now();

    els.docConvertBtn.disabled = true;
    els.docConvertBtn.classList.add('loading');
    if (els.docSelectedFile) {
        const fileSizeMb = (file.size / (1024 * 1024)).toFixed(2);
        els.docSelectedFile.textContent = `${file.name} (${fileSizeMb} MB)`;
    }
    if (els.docUploadSpeed) {
        els.docUploadSpeed.textContent = '0 KB/s';
    }
    if (els.docElapsedTime) {
        els.docElapsedTime.textContent = '0s';
    }
    if (els.docEtaTime) {
        els.docEtaTime.textContent = '--';
    }
    setUploadProgress(els, 0);
    setDocumentProgress(els, 0, 'Stage: upload');
    setStatus(els.docStatusArea, 'Converting document on server...', 'ok');

    try {
        const start = await startDocumentConversionJob(file, outputFormat, {
            documentType,
            outputProfile,
            debug,
            onUploadProgress: (info) => {
                setUploadProgress(els, info.percent || 0);
                if (els.docUploadSpeed) {
                    els.docUploadSpeed.textContent = formatBytesPerSecond(info.speedBps || 0);
                }
                if (els.docElapsedTime) {
                    els.docElapsedTime.textContent = formatDurationMs(Date.now() - startedAt);
                }
                if (els.docEtaTime && info.speedBps > 0 && info.total > info.loaded) {
                    const etaMs = ((info.total - info.loaded) / info.speedBps) * 1000;
                    els.docEtaTime.textContent = formatDurationMs(etaMs);
                }
            }
        });
        setUploadProgress(els, 100);
        let statusPayload = {
            jobId: start.jobId,
            status: start.status || 'queued',
            progress: start.progress || 5,
            stage: start.stage || 'queued',
            message: start.message || 'Job queued',
            conversionId: null
        };

        const deadline = Date.now() + 10 * 60 * 1000;
        while (statusPayload.status !== 'completed' && statusPayload.status !== 'failed') {
            if (Date.now() > deadline) {
                throw new Error('Conversion timed out. Please try again.');
            }

            const progress = statusPayload.progress || 0;
            setDocumentProgress(
                els,
                progress,
                `Stage: ${statusPayload.stage || 'processing'} (${progress}%)`
            );
            if (els.docElapsedTime) {
                const elapsedMs = Date.now() - startedAt;
                els.docElapsedTime.textContent = formatDurationMs(elapsedMs);
                if (els.docEtaTime) {
                    if (progress > 0 && progress < 100) {
                        const etaMs = (elapsedMs * (100 - progress)) / progress;
                        els.docEtaTime.textContent = formatDurationMs(etaMs);
                    } else if (progress >= 100) {
                        els.docEtaTime.textContent = '0s';
                    }
                }
            }
            statusPayload = await getDocumentConversionJobStatus(start.jobId);
            await sleep(800);
        }

        if (statusPayload.status === 'failed') {
            throw new Error(statusPayload.message || 'Document conversion failed.');
        }

        setDocumentProgress(els, 100, 'Stage: completed (100%)');
        if (els.docEtaTime) {
            els.docEtaTime.textContent = '0s';
        }
        const { blob, filename } = await downloadDocumentConversionJob(start.jobId);
        triggerDownload(blob, filename);
        setStatus(els.docStatusArea, `Success: downloaded ${filename}`, 'ok');

        if (debug && statusPayload.conversionId) {
            const debugPayload = await getDocumentDebug(statusPayload.conversionId);
            setDebugOutput(els, debugPayload.item || debugPayload);
        } else {
            setDebugOutput(els, null);
        }
    } catch (error) {
        setStatus(els.docStatusArea, `Error: ${error.message}`, 'error');
        if (!debug) {
            setDebugOutput(els, null);
        }
    } finally {
        els.docConvertBtn.disabled = false;
        els.docConvertBtn.classList.remove('loading');
    }
}

async function loadAudioFormatOptions(els) {
    const formats = await getAudioFormats();
    if (!Array.isArray(formats.output) || formats.output.length === 0) {
        return;
    }

    const current = els.audioOutputFormat.value;
    const values = normalizeFormats(formats.output);
    populateSelect(els.audioOutputFormat, values, current);
}

async function loadLibreOfficeFormatOptions(els) {
    const formats = await getLibreOfficeFormats();
    if (!Array.isArray(formats.output) || formats.output.length === 0) {
        return;
    }

    const current = els.loOutputFormat.value;
    const values = normalizeFormats(formats.output);
    populateSelect(els.loOutputFormat, values, current);
}

async function convertLibreOffice(els) {
    const file = els.loFile.files?.[0];
    if (!file) {
        setStatus(els.loStatusArea, 'Select a LibreOffice file before converting.', 'error');
        return;
    }

    const outputFormat = els.loOutputFormat.value;
    if (!outputFormat) {
        setStatus(els.loStatusArea, 'Choose an output format.', 'error');
        return;
    }

    els.loConvertBtn.disabled = true;
    els.loConvertBtn.classList.add('loading');
    setStatus(els.loStatusArea, 'Converting LibreOffice document on server...', 'ok');

    try {
        const { blob, filename } = await convertLibreOfficeOnline(file, outputFormat);
        triggerDownload(blob, filename);
        setStatus(els.loStatusArea, `Success: downloaded ${filename}`, 'ok');
    } catch (error) {
        setStatus(els.loStatusArea, `Error: ${error.message}`, 'error');
    } finally {
        els.loConvertBtn.disabled = false;
        els.loConvertBtn.classList.remove('loading');
    }
}

async function convertAudio(els) {
    const file = els.audioFile.files?.[0];
    if (!file) {
        setStatus(els.audioStatusArea, 'Select an audio file before converting.', 'error');
        return;
    }

    const outputFormat = els.audioOutputFormat.value;
    if (!outputFormat) {
        setStatus(els.audioStatusArea, 'Choose an output format.', 'error');
        return;
    }

    const bitrate = (els.audioBitrate.value || '').trim();
    els.audioConvertBtn.disabled = true;
    els.audioConvertBtn.classList.add('loading');
    setStatus(els.audioStatusArea, 'Converting audio on server...', 'ok');

    try {
        const { blob, filename } = await convertAudioOnline(file, outputFormat, { bitrate });
        triggerDownload(blob, filename);
        setStatus(els.audioStatusArea, `Success: downloaded ${filename}`, 'ok');
    } catch (error) {
        setStatus(els.audioStatusArea, `Error: ${error.message}`, 'error');
    } finally {
        els.audioConvertBtn.disabled = false;
        els.audioConvertBtn.classList.remove('loading');
    }
}

function renderStoredDocuments(els, items) {
    const selected = els.storedDocList.value;
    els.storedDocList.innerHTML = '';

    if (!Array.isArray(items) || items.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No documents stored';
        els.storedDocList.appendChild(option);
        return;
    }

    items.forEach((item) => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = `${item.name} (${item.originalFilename})`;
        els.storedDocList.appendChild(option);
    });

    if ([...els.storedDocList.options].some((option) => option.value === selected)) {
        els.storedDocList.value = selected;
    }
}

async function refreshStoredDocuments(els, silent = false) {
    try {
        const result = await listStoredDocuments();
        renderStoredDocuments(els, result.items);
        if (!silent) {
            setStatus(els.docLibraryStatusArea, `Loaded ${result.items.length} stored document(s).`, 'ok');
        }
    } catch (error) {
        if (!silent) {
            setStatus(els.docLibraryStatusArea, `Error: ${error.message}`, 'error');
        }
    }
}

async function storeCurrentDocument(els) {
    const file = els.storeDocFile.files?.[0];
    if (!file) {
        setStatus(els.docLibraryStatusArea, 'Select a file to store.', 'error');
        return;
    }

    try {
        await storeDocument(file, (els.storeDocName.value || '').trim());
        els.storeDocFile.value = '';
        await refreshStoredDocuments(els, true);
        setStatus(els.docLibraryStatusArea, 'Document stored for future users.', 'ok');
    } catch (error) {
        setStatus(els.docLibraryStatusArea, `Error: ${error.message}`, 'error');
    }
}

async function downloadSelectedDocument(els) {
    const id = els.storedDocList.value;
    if (!id) {
        setStatus(els.docLibraryStatusArea, 'Select a stored document to download.', 'error');
        return;
    }

    try {
        const { blob, filename } = await downloadStoredDocument(id);
        triggerDownload(blob, filename);
        setStatus(els.docLibraryStatusArea, `Downloaded ${filename}.`, 'ok');
    } catch (error) {
        setStatus(els.docLibraryStatusArea, `Error: ${error.message}`, 'error');
    }
}

async function deleteSelectedDocument(els) {
    const id = els.storedDocList.value;
    if (!id) {
        setStatus(els.docLibraryStatusArea, 'Select a stored document to delete.', 'error');
        return;
    }

    try {
        await deleteStoredDocument(id);
        await refreshStoredDocuments(els, true);
        setStatus(els.docLibraryStatusArea, 'Stored document deleted.', 'ok');
    } catch (error) {
        setStatus(els.docLibraryStatusArea, `Error: ${error.message}`, 'error');
    }
}

export function initUI() {
    const els = getElements();
    let docOptions = {
        defaultType: 'text',
        defaultProfile: 'modern',
        outputsByTypeAndProfile: {}
    };

    els.docConvertBtn.addEventListener('click', () => {
        void convertDocument(els, docOptions);
    });
    els.docFile.addEventListener('change', () => {
        const selected = els.docFile.files?.[0];
        if (!selected) {
            if (els.docSelectedFile) {
                els.docSelectedFile.textContent = 'No file selected';
            }
            return;
        }
        if (els.docSelectedFile) {
            const fileSizeMb = (selected.size / (1024 * 1024)).toFixed(2);
            els.docSelectedFile.textContent = `${selected.name} (${fileSizeMb} MB)`;
        }
    });
    els.loConvertBtn.addEventListener('click', () => {
        void convertLibreOffice(els);
    });
    els.audioConvertBtn.addEventListener('click', () => {
        void convertAudio(els);
    });
    els.storeDocBtn.addEventListener('click', () => {
        void storeCurrentDocument(els);
    });
    els.refreshDocListBtn.addEventListener('click', () => {
        void refreshStoredDocuments(els);
    });
    els.downloadDocBtn.addEventListener('click', () => {
        void downloadSelectedDocument(els);
    });
    els.deleteDocBtn.addEventListener('click', () => {
        void deleteSelectedDocument(els);
    });

    els.docType.addEventListener('change', () => {
        refreshOutputFormats(els, docOptions);
    });

    els.docOutputProfile.addEventListener('change', () => {
        refreshOutputFormats(els, docOptions);
    });

    if (els.docDebug) {
        els.docDebug.addEventListener('change', () => {
            if (!els.docDebug.checked) {
                setDebugOutput(els, null);
            }
        });
    }

    setStatus(els.docStatusArea, 'Ready. Start server and convert a document in browser.', 'ok');
    setDocumentProgress(els, 0, 'Progress: idle');
    setUploadProgress(els, 0);
    if (els.docSelectedFile) {
        els.docSelectedFile.textContent = 'No file selected';
    }
    if (els.docUploadSpeed) {
        els.docUploadSpeed.textContent = '0 KB/s';
    }
    if (els.docElapsedTime) {
        els.docElapsedTime.textContent = '0s';
    }
    if (els.docEtaTime) {
        els.docEtaTime.textContent = '--';
    }
    setStatus(els.loStatusArea, 'Ready. Upload a LibreOffice document to convert.', 'ok');
    setStatus(els.audioStatusArea, 'Ready. Upload audio to convert.', 'ok');
    setStatus(els.calcStatusArea, 'Ready. Enter values and run a calculation.', 'ok');
    initCalculator(els);
    setStatus(els.docLibraryStatusArea, 'Ready. Store documents for future users.', 'ok');
    setDebugOutput(els, null);

    void loadDocumentControls(els)
        .then((options) => {
            docOptions = options;
            setStatus(els.docStatusArea, 'Ready. Select type/profile and convert your document.', 'ok');
        })
        .catch((error) => {
            setStatus(els.docStatusArea, `Warning: ${error.message}`, 'error');
        });
    void loadAudioFormatOptions(els)
        .catch((error) => {
            setStatus(els.audioStatusArea, `Warning: ${error.message}`, 'error');
        });
    void loadLibreOfficeFormatOptions(els)
        .catch((error) => {
            setStatus(els.loStatusArea, `Warning: ${error.message}`, 'error');
        });
    void refreshStoredDocuments(els, true);

    initNavigation();
}
