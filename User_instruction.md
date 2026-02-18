# USERMD - DocConvert Pro User Guide

## For Normal Users

1. Open the app in browser.
2. Pick a tool from sidebar:
   - Document Converter
   - LibreOffice Formats
   - Audio Converter
   - PDF Tools
   - Document Library
   - API Access
3. Upload by:
   - selecting file,
   - drag/drop,
   - paste from clipboard.
4. Click convert/process.
5. Wait for progress and queue status if server is busy.
6. Download output when completed.

## Upload Status Details

In document upload area you can see:
- file size
- type
- last modified timestamp
- selected timestamp
- upload speed
- elapsed time
- remaining time
- progress bars/dots/text meter

## Document Library

- Store files for future users
- Browse folders in tree view
- Switch storage roots (Documents/Data/Snapshots)
- Download or delete selected items

## API Key Request

- Open **API Access**
- Enter name + email (+ purpose optional)
- Click **Request API Key**
- Save returned key immediately

## Admin Access

Admin is token-based.

1. Configure token in `config/admin_config.json`:

```json
{
  "admin_token": "your-token"
}
```

2. Restart server.
3. Open **Admin Diagnostics**.
4. Enter token and run diagnostics.

Admin diagnostics include:
- dependency checks
- binary checks (`soffice`, `ffmpeg`, `7z`)
- queue/job status
- storage and disk status
- analytics summary and performance duration stats
- recent failures
- API key inventory summary

## Network Access

To access from other devices on same LAN:
- run server on host machine
- open firewall for app/nginx port
- use `http://<host-lan-ip>:8000` (or port 80 with nginx)

## Troubleshooting

- If conversions fail, check **Admin Diagnostics**.
- If install fails on `pyheif`, use Python 3.12/3.11 or skip HEIF feature.
- Ensure LibreOffice (`soffice`) and FFmpeg are installed for full capability.
