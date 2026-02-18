function normalizeBoolean(input) {
    if (typeof input === 'boolean') {
        return input;
    }

    if (typeof input === 'string') {
        return ['1', 'true', 'yes', 'active'].includes(input.trim().toLowerCase());
    }

    return Boolean(input);
}

function splitFullName(name = '') {
    const clean = String(name).trim();
    if (!clean) {
        return { first: '', last: '' };
    }

    const parts = clean.split(/\s+/);
    return {
        first: parts[0] ?? '',
        last: parts.slice(1).join(' ')
    };
}

function toCanonical(record, version) {
    if (version === 'v1') {
        return {
            firstName: record.first_name ?? '',
            lastName: record.last_name ?? '',
            email: record.email ?? '',
            createdAt: record.created_at ?? '',
            active: normalizeBoolean(record.active ?? false)
        };
    }

    if (version === 'v2') {
        const names = splitFullName(record.fullName ?? '');
        return {
            firstName: names.first,
            lastName: names.last,
            email: record.emailAddress ?? '',
            createdAt: record.createdAt ?? '',
            active: normalizeBoolean(record.status ?? false)
        };
    }

    if (version === 'v3') {
        return {
            firstName: record.name?.first ?? '',
            lastName: record.name?.last ?? '',
            email: record.contact?.email ?? '',
            createdAt: record.meta?.createdAt ?? '',
            active: normalizeBoolean(record.meta?.active ?? false)
        };
    }

    throw new Error(`Unsupported input version: ${version}`);
}

function fromCanonical(model, version) {
    if (version === 'v1') {
        return {
            first_name: model.firstName,
            last_name: model.lastName,
            email: model.email,
            created_at: model.createdAt,
            active: model.active
        };
    }

    if (version === 'v2') {
        return {
            fullName: `${model.firstName} ${model.lastName}`.trim(),
            emailAddress: model.email,
            createdAt: model.createdAt,
            status: model.active ? 'active' : 'inactive'
        };
    }

    if (version === 'v3') {
        return {
            name: {
                first: model.firstName,
                last: model.lastName
            },
            contact: {
                email: model.email
            },
            meta: {
                createdAt: model.createdAt,
                active: model.active
            }
        };
    }

    throw new Error(`Unsupported output version: ${version}`);
}

export function mapVersion(record, sourceVersion, targetVersion) {
    const canonical = toCanonical(record, sourceVersion);
    return fromCanonical(canonical, targetVersion);
}
