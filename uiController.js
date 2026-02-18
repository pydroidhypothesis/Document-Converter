import {
    convertDocumentOnline,
    deleteStoredDocument,
    downloadStoredDocument,
    getDocumentDebug,
    getDocumentFormats,
    getDocumentOptions,
    listStoredDocuments,
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
        docStatusArea: document.getElementById('doc-status-area'),
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

function initNavigation() {
    const links = [...document.querySelectorAll('.sidebar-nav a[href^="#"]')];
    links.forEach((link) => {
        link.addEventListener('click', (event) => {
            const target = document.querySelector(link.getAttribute('href'));
            if (!target) {
                return;
            }
            event.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            links.forEach((item) => {
                const parent = item.closest('li');
                if (parent) {
                    parent.classList.toggle('active', item === link);
                }
            });
        });
    });
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

    els.docConvertBtn.disabled = true;
    els.docConvertBtn.classList.add('loading');
    setStatus(els.docStatusArea, 'Converting document on server...', 'ok');

    try {
        const { blob, filename, conversionId } = await convertDocumentOnline(file, outputFormat, {
            documentType,
            outputProfile,
            debug
        });
        triggerDownload(blob, filename);
        setStatus(els.docStatusArea, `Success: downloaded ${filename}`, 'ok');

        if (debug && conversionId) {
            const debugPayload = await getDocumentDebug(conversionId);
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
    void refreshStoredDocuments(els, true);

    initNavigation();
}
