import {
    parseCsv,
    stringifyCsv,
    parseNdjson,
    stringifyNdjson,
    parseKeyValue,
    stringifyKeyValue
} from './formatParsers.js';

const jsonHandler = {
    parse: (text) => JSON.parse(text),
    stringify: (value) => JSON.stringify(value, null, 2)
};

const csvHandler = {
    parse: (text) => parseCsv(text),
    stringify: (value) => stringifyCsv(value)
};

const ndjsonHandler = {
    parse: (text) => parseNdjson(text),
    stringify: (value) => stringifyNdjson(value)
};

const keyValueHandler = {
    parse: (text) => parseKeyValue(text),
    stringify: (value) => stringifyKeyValue(value)
};

export const converterRegistry = {
    json: jsonHandler,
    csv: csvHandler,
    ndjson: ndjsonHandler,
    keyvalue: keyValueHandler
};

export function getConverter(format) {
    const handler = converterRegistry[format];

    if (!handler) {
        throw new Error(`Unsupported format: ${format}`);
    }

    return handler;
}
