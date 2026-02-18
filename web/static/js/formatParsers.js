function splitCsvLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i += 1) {
        const char = line[i];
        const next = line[i + 1];

        if (char === '"') {
            if (inQuotes && next === '"') {
                current += '"';
                i += 1;
            } else {
                inQuotes = !inQuotes;
            }
            continue;
        }

        if (char === ',' && !inQuotes) {
            result.push(current);
            current = '';
            continue;
        }

        current += char;
    }

    result.push(current);
    return result;
}

function csvEscape(value) {
    const text = String(value ?? '');
    if (!/[",\n]/.test(text)) {
        return text;
    }
    return `"${text.replace(/"/g, '""')}"`;
}

export function parseCsv(text) {
    const trimmed = text.trim();
    if (!trimmed) {
        return [];
    }

    const lines = trimmed.split(/\r?\n/).filter((line) => line.trim() !== '');
    const headers = splitCsvLine(lines[0]);

    return lines.slice(1).map((line) => {
        const cells = splitCsvLine(line);
        const row = {};

        headers.forEach((header, index) => {
            row[header] = cells[index] ?? '';
        });

        return row;
    });
}

export function stringifyCsv(value) {
    const rows = Array.isArray(value) ? value : [value];
    if (rows.length === 0) {
        return '';
    }

    const headers = [...new Set(rows.flatMap((row) => Object.keys(row ?? {})))];
    const headerRow = headers.map(csvEscape).join(',');

    const dataRows = rows.map((row) => headers.map((header) => csvEscape(row?.[header])).join(','));

    return [headerRow, ...dataRows].join('\n');
}

export function parseNdjson(text) {
    const trimmed = text.trim();
    if (!trimmed) {
        return [];
    }

    return trimmed
        .split(/\r?\n/)
        .filter((line) => line.trim() !== '')
        .map((line) => JSON.parse(line));
}

export function stringifyNdjson(value) {
    const rows = Array.isArray(value) ? value : [value];
    return rows.map((row) => JSON.stringify(row)).join('\n');
}

export function parseKeyValue(text) {
    const output = {};

    text.split(/\r?\n/).forEach((line) => {
        const clean = line.trim();
        if (!clean || clean.startsWith('#')) {
            return;
        }

        const index = clean.indexOf('=');
        if (index < 0) {
            return;
        }

        const key = clean.slice(0, index).trim();
        const value = clean.slice(index + 1).trim();
        output[key] = value;
    });

    return output;
}

export function stringifyKeyValue(value) {
    const row = Array.isArray(value) ? value[0] ?? {} : value;

    return Object.entries(row ?? {})
        .map(([key, fieldValue]) => `${key}=${fieldValue ?? ''}`)
        .join('\n');
}
