import { getConverter } from './converterRegistry.js';
import { mapVersion } from './versionMappers.js';

function normalizeRecords(value) {
    if (Array.isArray(value)) {
        return value;
    }

    if (value !== null && typeof value === 'object') {
        return [value];
    }

    throw new Error('Input must be an object, array of objects, or supported tabular format.');
}

function maybeUnwrapSingle(records, outputFormat) {
    if (outputFormat === 'keyvalue') {
        return records[0] ?? {};
    }

    return records;
}

export function convertData(options) {
    const {
        inputText,
        inputFormat,
        outputFormat,
        inputVersion,
        outputVersion
    } = options;

    const inputConverter = getConverter(inputFormat);
    const outputConverter = getConverter(outputFormat);

    const parsed = inputConverter.parse(inputText);
    const records = normalizeRecords(parsed);

    const mapped = records.map((record) => mapVersion(record, inputVersion, outputVersion));
    const outputPayload = maybeUnwrapSingle(mapped, outputFormat);

    return {
        outputText: outputConverter.stringify(outputPayload),
        stats: {
            records: mapped.length,
            source: `${inputFormat}/${inputVersion}`,
            target: `${outputFormat}/${outputVersion}`
        }
    };
}

export function makeSampleData(format, version) {
    const sampleV1 = [
        {
            first_name: 'Ada',
            last_name: 'Lovelace',
            email: 'ada@example.com',
            created_at: '1843-12-10',
            active: true
        },
        {
            first_name: 'Alan',
            last_name: 'Turing',
            email: 'alan@example.com',
            created_at: '1936-06-01',
            active: false
        }
    ];

    const mapped = sampleV1.map((record) => mapVersion(record, 'v1', version));
    const payload = format === 'keyvalue' ? mapped[0] : mapped;

    return getConverter(format).stringify(payload);
}
