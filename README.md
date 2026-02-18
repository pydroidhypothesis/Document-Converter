# DocConvert Pro

DocConvert Pro is a web + CLI conversion toolkit with document/audio/PDF tools, storage browsing, queued conversions, admin diagnostics, and analytics.

## Features

- Document conversion with type/profile control (`legacy`, `modern`)
- Real-time upload + conversion progress (bars, text meters, queue position)
- Paste/drag-drop/click upload support with file detail preview
- LibreOffice format conversion
- Audio conversion
- PDF compress/decompress tools
- Document library with server-side storage and tree browsing
- Storage-root browser based on `config/storage_config.json`
- API key request module (`/api/apikey/request`)
- Admin diagnostics + analytics endpoints (token-protected)
- Queued batch processing for long-running conversion requests
- Archive conversion in `src` (zip/tar/tgz/tbz2/txz/gz/bz2/xz/7z)

## Project Layout

- Backend: `server.py`
- CLI entrypoint: `document_converter.py`
- Core modules: `src/`
- Active web UI templates/static: `web/templates`, `web/static`
- Config: `config/`

## Quick Start

### 1) Setup environment

```bash
./scripts/setup.sh
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure storage

Edit `config/storage_config.json`.

Example:

```json
{
  "storage": {
    "data_dir": "data",
    "snapshots_file": "data/snapshots.json",
    "documents_dir": "data/documents",
    "documents_index_file": "data/documents.json",
    "analytics_file": "data/analytics_events.csv",
    "api_keys_file": "data/api_keys.json"
  }
}
```

### 3) Configure admin token

Create `config/admin_config.json`:

```json
{
  "admin_token": "change-this-token"
}
```

Alternative: set env var `DOC_CONVERT_ADMIN_TOKEN`.

### 4) Run server

```bash
python server.py
```

Open `http://localhost:8000`.

## Nginx (Fedora)

Install and enable:

```bash
sudo dnf install -y nginx
sudo systemctl enable --now nginx
```

Use template: `config/nginx/docconvert-pro.conf`.

Deploy config:

```bash
sudo cp config/nginx/docconvert-pro.conf /etc/nginx/conf.d/docconvert-pro.conf
sudo nginx -t
sudo systemctl reload nginx
```

Open firewall:

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## API Endpoints (Key Ones)

- `POST /api/document/convert`
- `POST /api/document/convert/start`
- `GET /api/document/convert/status/<job_id>`
- `GET /api/document/convert/download/<job_id>`
- `GET /api/document/convert/queue`
- `POST /api/audio/convert`
- `POST /api/pdf/process`
- `GET /api/storage/config`
- `GET /api/storage/tree`
- `POST /api/apikey/request`

Admin-only (requires `X-Admin-Token`):

- `GET /api/admin/diagnostics`
- `GET /api/admin/analytics/summary`
- `GET /api/admin/analytics/export`

## CLI Usage

Convert files:

```bash
python document_converter.py convert input.docx --to pdf
python document_converter.py convert input.xlsx --to ods
```

Archive conversion example:

```bash
python document_converter.py convert sample.tar --to zip
python document_converter.py convert sample.tar --to "zip->tar.gz"
```

## Notes

- LibreOffice conversion requires `soffice` in PATH.
- Audio conversion requires `ffmpeg` for best compatibility with `pydub`.
- `pyheif` is conditional in requirements for Python compatibility.
