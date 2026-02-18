import { convertData, makeSampleData } from './converterService.js';
import { getDocumentFormats, convertDocumentOnline, convertDataOnline, triggerDownload } from './browserApi.js';

function getElements() {
    return {
        inputFormat: document.getElementById('input-format'),
        outputFormat: document.getElementById('output-format'),
        inputVersion: document.getElementById('input-version'),
        outputVersion: document.getElementById('output-version'),
        inputData: document.getElementById('input-data'),
        outputData: document.getElementById('output-data'),
        convertBtn: document.getElementById('convert-btn'),
        swapBtn: document.getElementById('swap-btn'),
        sampleBtn: document.getElementById('sample-btn'),
        clearBtn: document.getElementById('clear-btn'),
        statusArea: document.getElementById('status-area'),
        docFile: document.getElementById('doc-file'),
        docOutputFormat: document.getElementById('doc-output-format'),
        docConvertBtn: document.getElementById('doc-convert-btn'),
        docStatusArea: document.getElementById('doc-status-area')
    };
}

function setStatus(element, message, type = 'ok') {
    element.textContent = message;
    element.dataset.status = type;
}

async function performConversion(els) {
    const payload = {
        inputText: els.inputData.value,
        inputFormat: els.inputFormat.value,
        outputFormat: els.outputFormat.value,
        inputVersion: els.inputVersion.value,
        outputVersion: els.outputVersion.value
    };

    try {
        const result = await convertDataOnline(payload);

        els.outputData.value = result.outputText;
        setStatus(
            els.statusArea,
            `Success: ${result.stats.records} record(s) converted from ${result.stats.source} to ${result.stats.target}.`,
            'ok'
        );
    } catch (error) {
        try {
            const fallback = convertData(payload);
            els.outputData.value = fallback.outputText;
            setStatus(
                els.statusArea,
                `Server unavailable, used local converter. ${fallback.stats.records} record(s) converted.`,
                'ok'
            );
        } catch (fallbackError) {
            setStatus(els.statusArea, `Error: ${fallbackError.message || error.message}`, 'error');
        }
    }
}

function swapFormats(els) {
    const currentInputFormat = els.inputFormat.value;
    els.inputFormat.value = els.outputFormat.value;
    els.outputFormat.value = currentInputFormat;

    const currentInputVersion = els.inputVersion.value;
    els.inputVersion.value = els.outputVersion.value;
    els.outputVersion.value = currentInputVersion;

    const currentInput = els.inputData.value;
    els.inputData.value = els.outputData.value;
    els.outputData.value = currentInput;

    setStatus(els.statusArea, 'Formats and versions swapped.', 'ok');
}

function loadSample(els) {
    try {
        els.inputData.value = makeSampleData(els.inputFormat.value, els.inputVersion.value);
        setStatus(els.statusArea, 'Sample data loaded for selected input format and version.', 'ok');
    } catch (error) {
        setStatus(els.statusArea, `Error loading sample: ${error.message}`, 'error');
    }
}

function clearEditors(els) {
    els.inputData.value = '';
    els.outputData.value = '';
    setStatus(els.statusArea, 'Editors cleared.', 'ok');
}

function initNavigation() {
    const links = [...document.querySelectorAll('.sidebar-nav a[href^="#"]')];
    const sections = links
        .map((link) => document.querySelector(link.getAttribute('href')))
        .filter((section) => section);

    links.forEach((link) => {
        link.addEventListener('click', (event) => {
            const target = document.querySelector(link.getAttribute('href'));
            if (!target) {
                return;
            }
            event.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                const id = `#${entry.target.id}`;
                links.forEach((link) => {
                    const parent = link.closest('li');
                    if (!parent) {
                        return;
                    }
                    parent.classList.toggle('active', link.getAttribute('href') === id);
                });
            });
        },
        { threshold: 0.35 }
    );

    sections.forEach((section) => observer.observe(section));
}

async function loadDocumentFormatOptions(els) {
    try {
        const formats = await getDocumentFormats();
        if (!Array.isArray(formats.output) || formats.output.length === 0) {
            return;
        }

        const currentValue = els.docOutputFormat.value;
        els.docOutputFormat.innerHTML = '';

        formats.output.forEach((ext) => {
            const format = ext.replace(/^\./, '').toLowerCase();
            const option = document.createElement('option');
            option.value = format;
            option.textContent = format.toUpperCase();
            els.docOutputFormat.appendChild(option);
        });

        if ([...els.docOutputFormat.options].some((option) => option.value === currentValue)) {
            els.docOutputFormat.value = currentValue;
        }
    } catch (error) {
        setStatus(els.docStatusArea, `Warning: ${error.message}`, 'error');
    }
}

async function convertDocument(els) {
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

    els.docConvertBtn.disabled = true;
    els.docConvertBtn.classList.add('loading');
    setStatus(els.docStatusArea, 'Converting document on server...', 'ok');

    try {
        const { blob, filename } = await convertDocumentOnline(file, outputFormat);
        triggerDownload(blob, filename);
        setStatus(els.docStatusArea, `Success: downloaded ${filename}`, 'ok');
    } catch (error) {
        setStatus(els.docStatusArea, `Error: ${error.message}`, 'error');
    } finally {
        els.docConvertBtn.disabled = false;
        els.docConvertBtn.classList.remove('loading');
    }
}

export function initUI() {
    const els = getElements();

    els.convertBtn.addEventListener('click', () => {
        void performConversion(els);
    });
    els.swapBtn.addEventListener('click', () => swapFormats(els));
    els.sampleBtn.addEventListener('click', () => loadSample(els));
    els.clearBtn.addEventListener('click', () => clearEditors(els));
    els.docConvertBtn.addEventListener('click', () => {
        void convertDocument(els);
    });

    els.inputData.value = makeSampleData('json', 'v1');
    setStatus(els.statusArea, 'Ready. Click Convert to run the modular pipeline.', 'ok');
    setStatus(els.docStatusArea, 'Ready. Start server and convert a document in browser.', 'ok');
    void loadDocumentFormatOptions(els);
    initNavigation();
}
