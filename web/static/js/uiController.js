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
    getStorageConfig,
    getStorageTree,
    processPdfOnline,
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
        docUploadTextMeter: document.getElementById('doc-upload-textmeter'),
        docConversionTextMeter: document.getElementById('doc-conversion-textmeter'),
        docSelectedFile: document.getElementById('doc-selected-file'),
        docUploadSpeed: document.getElementById('doc-upload-speed'),
        docElapsedTime: document.getElementById('doc-elapsed-time'),
        docEtaTime: document.getElementById('doc-eta-time'),
        docStatusArea: document.getElementById('doc-status-area'),
        docVersionIndicator: document.getElementById('doc-version-indicator'),
        docVersionIcon: document.getElementById('doc-version-icon'),
        docVersionText: document.getElementById('doc-version-text'),
        docPasteZone: document.getElementById('doc-paste-zone'),
        docPasteHint: document.getElementById('doc-paste-hint'),
        loFile: document.getElementById('lo-file'),
        loOutputFormat: document.getElementById('lo-output-format'),
        loConvertBtn: document.getElementById('lo-convert-btn'),
        loStatusArea: document.getElementById('lo-status-area'),
        audioFile: document.getElementById('audio-file'),
        audioOutputFormat: document.getElementById('audio-output-format'),
        audioBitrate: document.getElementById('audio-bitrate'),
        audioConvertBtn: document.getElementById('audio-convert-btn'),
        audioStatusArea: document.getElementById('audio-status-area'),
        pdfFile: document.getElementById('pdf-file'),
        pdfMode: document.getElementById('pdf-mode'),
        pdfProcessBtn: document.getElementById('pdf-process-btn'),
        pdfStatusArea: document.getElementById('pdf-status-area'),
        calcRoot: document.getElementById('calc-root'),
        calcStatusArea: document.getElementById('calc-status-area'),
        storeDocFile: document.getElementById('store-doc-file'),
        storeDocName: document.getElementById('store-doc-name'),
        storedDocList: document.getElementById('stored-doc-list'),
        storeDocBtn: document.getElementById('store-doc-btn'),
        refreshDocListBtn: document.getElementById('refresh-doc-list-btn'),
        downloadDocBtn: document.getElementById('download-doc-btn'),
        deleteDocBtn: document.getElementById('delete-doc-btn'),
        docTreeUpBtn: document.getElementById('doc-tree-up-btn'),
        docTreeCurrentPath: document.getElementById('doc-tree-current-path'),
        docTreeList: document.getElementById('doc-tree-list'),
        storageRootSelect: document.getElementById('storage-root-select'),
        storageTreeRefreshBtn: document.getElementById('storage-tree-refresh-btn'),
        storageRootPath: document.getElementById('storage-root-path'),
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
    if (els.docConversionTextMeter) {
        els.docConversionTextMeter.textContent = formatHashMeter(safeValue);
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
    if (els.docUploadTextMeter) {
        els.docUploadTextMeter.textContent = formatHashMeter(safeValue);
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

function formatSelectedFileLabel(file) {
    if (!file) {
        return 'No file selected';
    }
    const fileSizeMb = (file.size / (1024 * 1024)).toFixed(2);
    return `${file.name} (${fileSizeMb} MB)`;
}

function getProfileMeta(profile) {
    const normalized = (profile || '').toLowerCase();
    if (normalized === 'legacy') {
        return {
            profile: 'legacy',
            iconClass: 'fas fa-scroll',
            label: 'Legacy Profile (v1)',
            shortLabel: 'LEGACY v1'
        };
    }
    return {
        profile: 'modern',
        iconClass: 'fas fa-bolt',
        label: 'Modern Profile (v2)',
        shortLabel: 'MODERN v2'
    };
}

function updateDocumentVersionIndicator(els, profile) {
    const meta = getProfileMeta(profile);
    if (els.docVersionIndicator) {
        els.docVersionIndicator.dataset.profile = meta.profile;
    }
    if (els.docVersionIcon) {
        els.docVersionIcon.className = meta.iconClass;
    }
    if (els.docVersionText) {
        els.docVersionText.textContent = meta.label;
    }
}

function formatHashMeter(value, width = 24) {
    const percent = Math.max(0, Math.min(100, Number(value) || 0));
    const filled = Math.round((percent / 100) * width);
    const meter = `${'#'.repeat(filled)}${'.'.repeat(width - filled)}`;
    return `[${meter}] ${Math.round(percent)}%`;
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

async function convertDocument(els, docOptions, file) {
    if (!file) {
        setStatus(els.docStatusArea, 'Select, paste, or drop a source file before converting.', 'error');
        return;
    }

    const outputFormat = els.docOutputFormat.value;
    if (!outputFormat) {
        setStatus(els.docStatusArea, 'Choose an output format.', 'error');
        return;
    }

    const documentType = els.docType.value || 'auto';
    const outputProfile = els.docOutputProfile.value || (docOptions.defaultProfile || 'modern');
    const profileMeta = getProfileMeta(outputProfile);
    const debug = Boolean(els.docDebug?.checked);
    const startedAt = Date.now();

    els.docConvertBtn.disabled = true;
    els.docConvertBtn.classList.add('loading');
    if (els.docSelectedFile) {
        els.docSelectedFile.textContent = formatSelectedFileLabel(file);
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
    setDocumentProgress(els, 0, `Stage: upload (${profileMeta.shortLabel})`);
    setStatus(els.docStatusArea, `Converting document on server using ${profileMeta.shortLabel}...`, 'ok');

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
                `Stage: ${statusPayload.stage || 'processing'} (${progress}%) - ${profileMeta.shortLabel}`
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

        setDocumentProgress(els, 100, `Stage: completed (100%) - ${profileMeta.shortLabel}`);
        if (els.docEtaTime) {
            els.docEtaTime.textContent = '0s';
        }
        const { blob, filename } = await downloadDocumentConversionJob(start.jobId);
        triggerDownload(blob, filename);
        setStatus(els.docStatusArea, `Success (${profileMeta.shortLabel}): downloaded ${filename}`, 'ok');

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

async function processPdf(els) {
    const file = els.pdfFile.files?.[0];
    if (!file) {
        setStatus(els.pdfStatusArea, 'Select a PDF file first.', 'error');
        return;
    }

    const mode = (els.pdfMode.value || 'compress').toLowerCase();
    if (!['compress', 'decompress'].includes(mode)) {
        setStatus(els.pdfStatusArea, 'Choose a valid PDF operation.', 'error');
        return;
    }

    els.pdfProcessBtn.disabled = true;
    els.pdfProcessBtn.classList.add('loading');
    setStatus(els.pdfStatusArea, `${mode === 'compress' ? 'Compressing' : 'Decompressing'} PDF on server...`, 'ok');

    try {
        const { blob, filename } = await processPdfOnline(file, mode);
        triggerDownload(blob, filename);
        setStatus(els.pdfStatusArea, `Success: downloaded ${filename}`, 'ok');
    } catch (error) {
        setStatus(els.pdfStatusArea, `Error: ${error.message}`, 'error');
    } finally {
        els.pdfProcessBtn.disabled = false;
        els.pdfProcessBtn.classList.remove('loading');
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

async function loadStorageRoots(els, state) {
    if (!els.storageRootSelect) {
        return;
    }

    const payload = await getStorageConfig();
    const roots = Array.isArray(payload.roots) ? payload.roots : [];
    const current = state.root || els.storageRootSelect.value || 'documents';

    els.storageRootSelect.innerHTML = '';
    roots.forEach((root) => {
        const option = document.createElement('option');
        option.value = root.key;
        option.textContent = root.label;
        els.storageRootSelect.appendChild(option);
    });

    if ([...els.storageRootSelect.options].some((option) => option.value === current)) {
        els.storageRootSelect.value = current;
    } else if (els.storageRootSelect.options.length > 0) {
        els.storageRootSelect.selectedIndex = 0;
    }

    state.root = els.storageRootSelect.value || 'documents';
    state.path = '';

    if (els.storageRootPath) {
        const selected = roots.find((item) => item.key === state.root);
        els.storageRootPath.textContent = `Root: ${selected?.path || '-'}`;
    }
}

function renderDocumentTree(els, tree, navigateTo) {
    if (!els.docTreeList) {
        return;
    }

    const current = tree.currentPath || '';
    const rootKey = (tree.rootKey || 'documents').toLowerCase();
    if (els.docTreeCurrentPath) {
        els.docTreeCurrentPath.textContent = `${rootKey}/${current ? `${current}/` : ''}`;
    }
    if (els.storageRootPath) {
        els.storageRootPath.textContent = `Root: ${tree.root || '-'}`;
    }
    if (els.docTreeUpBtn) {
        els.docTreeUpBtn.disabled = tree.parentPath === null;
    }

    els.docTreeList.innerHTML = '';
    if (!Array.isArray(tree.entries) || tree.entries.length === 0) {
        const empty = document.createElement('div');
        empty.textContent = '└─ (empty folder)';
        els.docTreeList.appendChild(empty);
        return;
    }

    tree.entries.forEach((entry, index) => {
        const row = document.createElement('div');
        const branch = index === tree.entries.length - 1 ? '└─' : '├─';
        if (entry.type === 'folder') {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'action-btn';
            button.style.margin = '2px 0';
            button.textContent = `${branch} 📁 ${entry.name}/ (${entry.sizeReadable || '-'})`;
            button.addEventListener('click', () => navigateTo(entry.path));
            row.appendChild(button);
        } else {
            row.textContent = `${branch} 📄 ${entry.name} (${entry.sizeReadable || '-'})`;
        }
        els.docTreeList.appendChild(row);
    });
}

async function loadDocumentTree(els, root = 'documents', path = '', silent = false) {
    try {
        const tree = await getStorageTree(root, path);
        if (els.docTreeList) {
            els.docTreeList.dataset.currentPath = tree.currentPath || '';
            els.docTreeList.dataset.root = root;
        }
        renderDocumentTree(els, tree, async (nextPath) => {
            await loadDocumentTree(els, root, nextPath);
        });

        if (els.docTreeUpBtn) {
            els.docTreeUpBtn.onclick = () => {
                void loadDocumentTree(els, root, tree.parentPath || '');
            };
        }

        if (!silent) {
            setStatus(els.docLibraryStatusArea, `Opened folder: ${root}/${tree.currentPath || ''}`, 'ok');
        }
    } catch (error) {
        if (!silent) {
            setStatus(els.docLibraryStatusArea, `Error: ${error.message}`, 'error');
        }
    }
}

function getSelectedStorageRoot(els) {
    return (els.storageRootSelect?.value || 'documents').toLowerCase();
}

function getCurrentTreePath(els) {
    return els.docTreeList?.dataset.currentPath || '';
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
        await loadDocumentTree(els, getSelectedStorageRoot(els), getCurrentTreePath(els), true);
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
        await loadDocumentTree(els, getSelectedStorageRoot(els), getCurrentTreePath(els), true);
        setStatus(els.docLibraryStatusArea, 'Stored document deleted.', 'ok');
    } catch (error) {
        setStatus(els.docLibraryStatusArea, `Error: ${error.message}`, 'error');
    }
}

function extractFileFromClipboardEvent(event) {
    const items = event.clipboardData?.items || [];
    for (const item of items) {
        if (item.kind === 'file') {
            const file = item.getAsFile();
            if (file) {
                return file;
            }
        }
    }
    return null;
}

export function initUI() {
    const els = getElements();
    let docOptions = {
        defaultType: 'text',
        defaultProfile: 'modern',
        outputsByTypeAndProfile: {}
    };
    let selectedDocumentFile = null;
    const storageBrowserState = {
        root: 'documents',
        path: ''
    };

    const updateSelectedDocument = (file, source = 'picker') => {
        selectedDocumentFile = file || null;

        if (els.docSelectedFile) {
            els.docSelectedFile.textContent = formatSelectedFileLabel(selectedDocumentFile);
        }
        if (els.docPasteZone) {
            els.docPasteZone.classList.toggle('is-has-file', Boolean(selectedDocumentFile));
            els.docPasteZone.classList.remove('is-active');
        }
        if (els.docPasteHint) {
            if (!selectedDocumentFile) {
                els.docPasteHint.textContent = 'Press Ctrl+V after copying a document file, or drag and drop it here.';
            } else if (source === 'paste') {
                els.docPasteHint.textContent = `Pasted file: ${selectedDocumentFile.name}`;
            } else if (source === 'drop') {
                els.docPasteHint.textContent = `Dropped file: ${selectedDocumentFile.name}`;
            } else {
                els.docPasteHint.textContent = `Selected file: ${selectedDocumentFile.name}`;
            }
        }
    };

    const getCurrentDocumentFile = () => selectedDocumentFile || els.docFile.files?.[0] || null;

    const isDocumentConverterVisible = () => {
        const section = document.getElementById('document-converter');
        return Boolean(section && section.style.display !== 'none');
    };

    els.docConvertBtn.addEventListener('click', () => {
        void convertDocument(els, docOptions, getCurrentDocumentFile());
    });
    els.docFile.addEventListener('change', () => {
        updateSelectedDocument(els.docFile.files?.[0] || null, 'picker');
    });

    if (els.docPasteZone) {
        els.docPasteZone.addEventListener('click', () => {
            els.docFile.click();
        });
        els.docPasteZone.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                els.docFile.click();
            }
        });
        ['dragenter', 'dragover'].forEach((eventName) => {
            els.docPasteZone.addEventListener(eventName, (event) => {
                event.preventDefault();
                event.stopPropagation();
                els.docPasteZone.classList.add('is-active');
            });
        });
        ['dragleave', 'dragend'].forEach((eventName) => {
            els.docPasteZone.addEventListener(eventName, (event) => {
                event.preventDefault();
                event.stopPropagation();
                els.docPasteZone.classList.remove('is-active');
            });
        });
        els.docPasteZone.addEventListener('drop', (event) => {
            event.preventDefault();
            event.stopPropagation();
            const droppedFile = event.dataTransfer?.files?.[0] || null;
            updateSelectedDocument(droppedFile, droppedFile ? 'drop' : 'picker');
        });
        els.docPasteZone.addEventListener('paste', (event) => {
            const pastedFile = extractFileFromClipboardEvent(event);
            if (!pastedFile) {
                return;
            }
            event.preventDefault();
            updateSelectedDocument(pastedFile, 'paste');
        });
    }

    window.addEventListener('paste', (event) => {
        if (!isDocumentConverterVisible()) {
            return;
        }
        const pastedFile = extractFileFromClipboardEvent(event);
        if (!pastedFile) {
            return;
        }
        event.preventDefault();
        updateSelectedDocument(pastedFile, 'paste');
    });

    els.loConvertBtn.addEventListener('click', () => {
        void convertLibreOffice(els);
    });
    els.audioConvertBtn.addEventListener('click', () => {
        void convertAudio(els);
    });
    els.pdfProcessBtn.addEventListener('click', () => {
        void processPdf(els);
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
    if (els.storageRootSelect) {
        els.storageRootSelect.addEventListener('change', () => {
            storageBrowserState.root = getSelectedStorageRoot(els);
            storageBrowserState.path = '';
            void loadDocumentTree(els, storageBrowserState.root, storageBrowserState.path);
        });
    }
    if (els.storageTreeRefreshBtn) {
        els.storageTreeRefreshBtn.addEventListener('click', () => {
            storageBrowserState.root = getSelectedStorageRoot(els);
            storageBrowserState.path = getCurrentTreePath(els);
            void loadDocumentTree(els, storageBrowserState.root, storageBrowserState.path);
        });
    }
    els.docType.addEventListener('change', () => {
        refreshOutputFormats(els, docOptions);
    });

    els.docOutputProfile.addEventListener('change', () => {
        updateDocumentVersionIndicator(els, els.docOutputProfile.value);
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
    updateDocumentVersionIndicator(els, els.docOutputProfile.value || 'modern');
    setDocumentProgress(els, 0, 'Stage: idle');
    setUploadProgress(els, 0);
    updateSelectedDocument(null);
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
    setStatus(els.pdfStatusArea, 'Ready. Upload a PDF file and run compression or decompression.', 'ok');
    setStatus(els.calcStatusArea, 'Ready. Enter values and run a calculation.', 'ok');
    initCalculator(els);
    setStatus(els.docLibraryStatusArea, 'Ready. Store documents for future users.', 'ok');
    setDebugOutput(els, null);

    void loadDocumentControls(els)
        .then((options) => {
            docOptions = options;
            updateDocumentVersionIndicator(els, els.docOutputProfile.value || options.defaultProfile || 'modern');
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
    void loadStorageRoots(els, storageBrowserState)
        .then(() => {
            storageBrowserState.root = getSelectedStorageRoot(els);
            storageBrowserState.path = '';
            return loadDocumentTree(els, storageBrowserState.root, storageBrowserState.path, true);
        })
        .catch((_error) => {
            void loadDocumentTree(els, 'documents', '', true);
        });

    initNavigation();
}
