function getErrorMessage(payload, fallback) {
    if (!payload) {
        return fallback;
    }

    if (typeof payload === 'string') {
        return payload;
    }

    if (payload.message) {
        return payload.message;
    }

    if (payload.error) {
        return payload.error;
    }

    return fallback;
}

export async function getDocumentFormats() {
    const response = await fetch('/api/formats/document');
    if (!response.ok) {
        throw new Error('Failed to load document formats from server.');
    }

    return response.json();
}

export async function getLibreOfficeFormats() {
    const response = await fetch('/api/formats/libreoffice');
    if (!response.ok) {
        throw new Error('Failed to load LibreOffice formats from server.');
    }
    return response.json();
}

export async function getAudioFormats() {
    const response = await fetch('/api/formats/audio');
    if (!response.ok) {
        throw new Error('Failed to load audio formats from server.');
    }
    return response.json();
}

export async function getDocumentOptions() {
    const response = await fetch('/api/formats/document/options');
    if (!response.ok) {
        throw new Error('Failed to load document options from server.');
    }
    return response.json();
}

export async function getDocumentDebug(conversionId) {
    const response = await fetch(`/api/document/debug/${encodeURIComponent(conversionId)}`);
    if (!response.ok) {
        let body = null;
        try {
            body = await response.json();
        } catch (_error) {
            body = null;
        }
        throw new Error(getErrorMessage(body, 'Failed to load debug details.'));
    }
    return response.json();
}

export async function listStoredDocuments() {
    const response = await fetch('/api/document/store');
    if (!response.ok) {
        throw new Error('Failed to load stored documents.');
    }
    return response.json();
}

export async function getStoredDocumentTree(path = '') {
    const query = path ? `?path=${encodeURIComponent(path)}` : '';
    const response = await fetch(`/api/document/store/tree${query}`);
    if (!response.ok) {
        let body = null;
        try {
            body = await response.json();
        } catch (_error) {
            body = null;
        }
        throw new Error(getErrorMessage(body, 'Failed to load folder tree.'));
    }
    return response.json();
}

export async function getStorageConfig() {
    const response = await fetch('/api/storage/config');
    if (!response.ok) {
        throw new Error('Failed to load storage configuration.');
    }
    return response.json();
}

export async function getStorageTree(root = 'documents', path = '') {
    const query = new URLSearchParams();
    query.set('root', root);
    if (path) {
        query.set('path', path);
    }

    const response = await fetch(`/api/storage/tree?${query.toString()}`);
    if (!response.ok) {
        let body = null;
        try {
            body = await response.json();
        } catch (_error) {
            body = null;
        }
        throw new Error(getErrorMessage(body, 'Failed to load storage tree.'));
    }
    return response.json();
}

export async function storeDocument(file, name = '') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);

    const response = await fetch('/api/document/store', {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        let body = null;
        try {
            body = await response.json();
        } catch (_error) {
            body = null;
        }
        throw new Error(getErrorMessage(body, 'Failed to store document.'));
    }

    return response.json();
}

export async function downloadStoredDocument(documentId) {
    const response = await fetch(`/api/document/store/${encodeURIComponent(documentId)}/download`);
    if (!response.ok) {
        let body = null;
        try {
            body = await response.json();
        } catch (_error) {
            body = null;
        }
        throw new Error(getErrorMessage(body, 'Failed to download stored document.'));
    }

    const blob = await response.blob();
    const disposition = response.headers.get('content-disposition') || '';
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : 'stored-document';
    return { blob, filename };
}

export async function deleteStoredDocument(documentId) {
    const response = await fetch(`/api/document/store/${encodeURIComponent(documentId)}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        let body = null;
        try {
            body = await response.json();
        } catch (_error) {
            body = null;
        }
        throw new Error(getErrorMessage(body, 'Failed to delete stored document.'));
    }
    return response.json();
}

export async function convertDocumentOnline(file, outputFormat, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', outputFormat);
    formData.append('document_type', options.documentType || 'auto');
    formData.append('output_profile', options.outputProfile || 'modern');
    formData.append('debug', options.debug ? 'true' : 'false');

    const response = await fetch('/api/document/convert', {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        let payload = null;
        try {
            payload = await response.json();
        } catch (_error) {
            payload = null;
        }

        throw new Error(getErrorMessage(payload, 'Document conversion failed.'));
    }

    const blob = await response.blob();
    const disposition = response.headers.get('content-disposition') || '';
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : `converted.${outputFormat}`;
    const conversionId = response.headers.get('x-conversion-id') || '';

    return { blob, filename, conversionId };
}

export async function startDocumentConversionJob(file, outputFormat, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', outputFormat);
    formData.append('document_type', options.documentType || 'auto');
    formData.append('output_profile', options.outputProfile || 'modern');
    formData.append('debug', options.debug ? 'true' : 'false');

    const uploadStartedAt = Date.now();
    const onUploadProgress = typeof options.onUploadProgress === 'function' ? options.onUploadProgress : null;

    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/document/convert/start');

        xhr.upload.onprogress = (event) => {
            if (!onUploadProgress || !event.lengthComputable) {
                return;
            }
            const elapsedMs = Math.max(1, Date.now() - uploadStartedAt);
            const loaded = event.loaded || 0;
            const total = event.total || 0;
            onUploadProgress({
                loaded,
                total,
                percent: total > 0 ? (loaded / total) * 100 : 0,
                elapsedMs,
                speedBps: loaded / (elapsedMs / 1000)
            });
        };

        xhr.onerror = () => {
            reject(new Error('Failed to start conversion job.'));
        };

        xhr.onload = () => {
            let payload = null;
            try {
                payload = JSON.parse(xhr.responseText || '{}');
            } catch (_error) {
                payload = null;
            }

            if (xhr.status < 200 || xhr.status >= 300) {
                reject(new Error(getErrorMessage(payload, 'Failed to start conversion job.')));
                return;
            }

            resolve(payload);
        };

        xhr.send(formData);
    });
}

export async function getDocumentConversionJobStatus(jobId) {
    const response = await fetch(`/api/document/convert/status/${encodeURIComponent(jobId)}`);
    if (!response.ok) {
        let payload = null;
        try {
            payload = await response.json();
        } catch (_error) {
            payload = null;
        }
        throw new Error(getErrorMessage(payload, 'Failed to get conversion status.'));
    }
    return response.json();
}

export async function downloadDocumentConversionJob(jobId) {
    const response = await fetch(`/api/document/convert/download/${encodeURIComponent(jobId)}`);
    if (!response.ok) {
        let payload = null;
        try {
            payload = await response.json();
        } catch (_error) {
            payload = null;
        }
        throw new Error(getErrorMessage(payload, 'Failed to download converted file.'));
    }

    const blob = await response.blob();
    const disposition = response.headers.get('content-disposition') || '';
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : 'converted-file';
    return { blob, filename };
}

export async function convertLibreOfficeOnline(file, outputFormat) {
    return convertDocumentOnline(file, outputFormat, {
        documentType: 'auto',
        outputProfile: 'modern',
        debug: false
    });
}

export async function convertAudioOnline(file, outputFormat, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', outputFormat);
    if (options.bitrate) {
        formData.append('bitrate', options.bitrate);
    }

    const response = await fetch('/api/audio/convert', {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        let payload = null;
        try {
            payload = await response.json();
        } catch (_error) {
            payload = null;
        }
        throw new Error(getErrorMessage(payload, 'Audio conversion failed.'));
    }

    const blob = await response.blob();
    const disposition = response.headers.get('content-disposition') || '';
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : `converted.${outputFormat}`;

    return { blob, filename };
}

export async function processPdfOnline(file, mode = 'compress') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);

    const response = await fetch('/api/pdf/process', {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        let payload = null;
        try {
            payload = await response.json();
        } catch (_error) {
            payload = null;
        }
        throw new Error(getErrorMessage(payload, 'PDF processing failed.'));
    }

    const blob = await response.blob();
    const disposition = response.headers.get('content-disposition') || '';
    const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
    const filename = match ? match[1] : 'processed.pdf';

    return { blob, filename };
}

export async function convertDataOnline(payload) {
    const response = await fetch('/api/data/convert', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        let body = null;
        try {
            body = await response.json();
        } catch (_error) {
            body = null;
        }
        throw new Error(getErrorMessage(body, 'Data conversion failed.'));
    }

    return response.json();
}

export async function listDataSnapshots() {
    const response = await fetch('/api/data/store');
    if (!response.ok) {
        throw new Error('Failed to load saved data.');
    }
    return response.json();
}

export async function saveDataSnapshot(payload) {
    const response = await fetch('/api/data/store', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        let body = null;
        try {
            body = await response.json();
        } catch (_error) {
            body = null;
        }
        throw new Error(getErrorMessage(body, 'Failed to save data on server.'));
    }

    return response.json();
}

export async function getDataSnapshot(id) {
    const response = await fetch(`/api/data/store/${encodeURIComponent(id)}`);
    if (!response.ok) {
        let body = null;
        try {
            body = await response.json();
        } catch (_error) {
            body = null;
        }
        throw new Error(getErrorMessage(body, 'Failed to load saved data.'));
    }
    return response.json();
}

export async function deleteDataSnapshot(id) {
    const response = await fetch(`/api/data/store/${encodeURIComponent(id)}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        let body = null;
        try {
            body = await response.json();
        } catch (_error) {
            body = null;
        }
        throw new Error(getErrorMessage(body, 'Failed to delete saved data.'));
    }
    return response.json();
}

export function triggerDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}
