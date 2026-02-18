# DocConvert Pro

Modular conversion toolkit for converting data from one format/version to another.

## Objective

- Keep a modular architecture.
- Convert data formats (web module).
- Convert office files (CLI module) including PDF, Word, Excel, Publisher and LibreOffice formats.

## Modules

### 1) Web Data Converter (JavaScript)

Pipeline:
1. Parse input format
2. Map version (`v1`/`v2`/`v3`)
3. Serialize output format

Files:
- `main/app.js`
- `main/uiController.js`
- `main/converterService.js`
- `main/converterRegistry.js`
- `main/formatParsers.js`
- `main/versionMappers.js`
- `main/index.html`
- `main/style.css`

Supported data formats:
- `json`
- `csv`
- `ndjson`
- `keyvalue`

### 2) Document Converter (Python + LibreOffice)

Main files:
- `main/document_converter.py` (CLI entrypoint)
- `main/src/converters/document_converters.py` (DocumentConverter module)

DocumentConverter supports LibreOffice-backed conversions for:
- Word/Text: `doc`, `docx`, `odt`, `ott`, `rtf`, `txt`, `html`, `xml`
- Spreadsheet: `xls`, `xlsx`, `ods`, `ots`, `csv`, `fods`
- Presentation: `ppt`, `pptx`, `odp`, `otp`, `fodp`
- Other: `pdf`, `epub`, `pub`

Note: Publisher (`.pub`) support depends on LibreOffice import capabilities for the source file.

## How To Run

### Start Backend Server (browser conversion)

Run from `/home/liveuser/Documents/main`:

```bash
python server.py
```

Then open:

- `http://localhost:8000`

This enables online document conversion in browser via:
- `POST /api/document/convert`
- `GET /api/formats/document`

### Web UI

1. Start backend with `python server.py`.
2. Open `http://localhost:8000`.
3. Use **Online Document Converter** for file upload/download conversion.
4. Use **Data Workspace** for structured data conversion.

### CLI Document Conversion

Run from `/home/liveuser/Documents/main`:

```bash
python document_converter.py convert input.docx --to pdf
python document_converter.py convert input.xlsx --to ods
python document_converter.py convert input.pub --to pdf
```

Optional output path:

```bash
python document_converter.py convert input.pptx --to odp --output output_file.odp
```

## Requirements

- Python dependencies from `main/requirements.txt`
- LibreOffice installed and available in `PATH` as `soffice`

## Validation

JavaScript syntax checks:

```bash
node --check main/app.js
node --check main/uiController.js
node --check main/converterService.js
node --check main/versionMappers.js
node --check main/formatParsers.js
node --check main/converterRegistry.js
```

Python syntax checks:

```bash
python -m py_compile main/document_converter.py main/src/converters/document_converters.py
```

## Notes

- Existing folder/file structure is preserved.
- Files/folders were not removed.
- Implementation stays modular by separating UI, service, registry, parser, mapper, and converter classes.
