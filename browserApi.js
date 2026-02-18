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
