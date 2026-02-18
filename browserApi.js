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

export async function convertDocumentOnline(file, outputFormat) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', outputFormat);

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
