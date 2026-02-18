#!/usr/bin/env python3
"""Web server for browser-based conversion."""

import csv
import io
import json
import tempfile
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory, after_this_request
from werkzeug.utils import secure_filename

from document_converter import ConversionToolkit


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_STORE_FILE = DATA_DIR / "snapshots.json"
DOCUMENT_STORE_DIR = DATA_DIR / "documents"
DOCUMENT_STORE_INDEX = DATA_DIR / "documents.json"
DOCUMENT_TYPE_INPUTS = {
    "text": {".txt", ".rtf", ".doc", ".docx", ".odt", ".ott", ".sxw", ".html", ".htm", ".xml", ".epub", ".fodt"},
    "spreadsheet": {".xls", ".xlsx", ".ods", ".ots", ".csv", ".fods"},
    "presentation": {".ppt", ".pptx", ".odp", ".otp", ".fodp"},
    "publisher": {".pub"}
}
OUTPUT_PROFILE_FORMATS = {
    "text": {
        "legacy": [".pdf", ".txt", ".rtf", ".doc", ".html", ".xml"],
        "modern": [".pdf", ".txt", ".docx", ".odt", ".html", ".xml", ".epub"]
    },
    "spreadsheet": {
        "legacy": [".pdf", ".xls", ".csv"],
        "modern": [".pdf", ".xlsx", ".ods", ".csv"]
    },
    "presentation": {
        "legacy": [".pdf", ".ppt"],
        "modern": [".pdf", ".pptx", ".odp"]
    },
    "publisher": {
        "legacy": [".pdf"],
        "modern": [".pdf", ".epub"]
    }
}
DEBUG_HISTORY_LIMIT = 100
DEBUG_HISTORY = []
app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")
toolkit = ConversionToolkit()


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/formats/document")
def document_formats():
    return jsonify(toolkit.document_converter.supported_formats)


def _detect_document_type(ext: str):
    for doc_type, extensions in DOCUMENT_TYPE_INPUTS.items():
        if ext in extensions:
            return doc_type
    return None


def _get_output_formats_for(doc_type: str, output_profile: str):
    return OUTPUT_PROFILE_FORMATS.get(doc_type, {}).get(output_profile, [])


def _store_debug_entry(entry):
    DEBUG_HISTORY.append(entry)
    if len(DEBUG_HISTORY) > DEBUG_HISTORY_LIMIT:
        del DEBUG_HISTORY[:-DEBUG_HISTORY_LIMIT]


@app.get("/api/formats/document/options")
def document_options():
    return jsonify({
        "types": sorted(OUTPUT_PROFILE_FORMATS.keys()),
        "profiles": ["legacy", "modern"],
        "defaultType": "text",
        "defaultProfile": "modern",
        "outputsByTypeAndProfile": OUTPUT_PROFILE_FORMATS
    })


@app.get("/api/document/debug/<conversion_id>")
def get_document_debug(conversion_id: str):
    entry = next((item for item in reversed(DEBUG_HISTORY) if item.get("conversionId") == conversion_id), None)
    if not entry:
        return jsonify({"message": "Debug entry not found"}), 404
    return jsonify({"item": entry})


@app.get("/api/document/store")
def list_stored_documents():
    items = _load_stored_documents()
    items.sort(key=lambda item: item.get("createdAt", ""), reverse=True)
    return jsonify({"items": items})


@app.post("/api/document/store")
def store_document():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "Missing uploaded file"}), 400

    source = request.files["file"]
    if source.filename is None or source.filename.strip() == "":
        return jsonify({"success": False, "message": "Invalid source filename"}), 400

    safe_name = secure_filename(source.filename)
    if not safe_name:
        safe_name = "document"

    document_id = uuid.uuid4().hex
    stored_name = f"{document_id}_{safe_name}"
    DOCUMENT_STORE_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = DOCUMENT_STORE_DIR / stored_name
    source.save(stored_path)

    item = {
        "id": document_id,
        "name": (request.form.get("name") or "").strip() or safe_name,
        "originalFilename": safe_name,
        "storedFilename": stored_name,
        "sizeBytes": stored_path.stat().st_size,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }

    items = _load_stored_documents()
    items.append(item)
    _save_stored_documents(items)
    return jsonify({"item": item}), 201


@app.get("/api/document/store/<document_id>/download")
def download_stored_document(document_id: str):
    items = _load_stored_documents()
    item = next((entry for entry in items if entry.get("id") == document_id), None)
    if not item:
        return jsonify({"message": "Stored document not found"}), 404

    path = DOCUMENT_STORE_DIR / item["storedFilename"]
    if not path.exists():
        return jsonify({"message": "Stored file missing on disk"}), 404

    return send_file(path, as_attachment=True, download_name=item.get("originalFilename", path.name))


@app.delete("/api/document/store/<document_id>")
def delete_stored_document(document_id: str):
    items = _load_stored_documents()
    item = next((entry for entry in items if entry.get("id") == document_id), None)
    if not item:
        return jsonify({"message": "Stored document not found"}), 404

    filtered = [entry for entry in items if entry.get("id") != document_id]
    _save_stored_documents(filtered)

    path = DOCUMENT_STORE_DIR / item.get("storedFilename", "")
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass

    return jsonify({"success": True})


@app.post("/api/document/convert")
def convert_document():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "Missing uploaded file"}), 400

    source = request.files["file"]
    output_format = (request.form.get("output_format") or "").strip().lower()
    selected_type = (request.form.get("document_type") or "auto").strip().lower()
    output_profile = (request.form.get("output_profile") or "modern").strip().lower()
    debug_mode = (request.form.get("debug") or "").strip().lower() in {"1", "true", "yes", "on"}

    if not output_format:
        return jsonify({"success": False, "message": "Missing output format"}), 400

    if not output_format.startswith("."):
        output_format = f".{output_format}"

    if source.filename is None or source.filename.strip() == "":
        return jsonify({"success": False, "message": "Invalid source filename"}), 400

    safe_name = secure_filename(source.filename)
    if not safe_name:
        safe_name = "upload"

    temp_dir = Path(tempfile.mkdtemp(prefix="docconvert_"))
    input_path = temp_dir / safe_name
    source.save(input_path)
    conversion_id = uuid.uuid4().hex
    started = time.perf_counter()

    detected_type = _detect_document_type(input_path.suffix.lower())
    if not detected_type:
        return jsonify({
            "success": False,
            "message": f"Unsupported source file type: {input_path.suffix.lower() or '(none)'}"
        }), 400

    if selected_type != "auto" and selected_type not in OUTPUT_PROFILE_FORMATS:
        return jsonify({"success": False, "message": f"Unsupported document type: {selected_type}"}), 400

    if output_profile not in {"legacy", "modern"}:
        return jsonify({"success": False, "message": f"Unsupported output profile: {output_profile}"}), 400

    effective_type = detected_type if selected_type == "auto" else selected_type
    if selected_type != "auto" and selected_type != detected_type:
        return jsonify({
            "success": False,
            "message": f"File type mismatch. Uploaded file is {detected_type}, selected type is {selected_type}."
        }), 400

    allowed_outputs = _get_output_formats_for(effective_type, output_profile)
    if output_format not in allowed_outputs:
        return jsonify({
            "success": False,
            "message": (
                f"Output format {output_format} is not allowed for type {effective_type} "
                f"with profile {output_profile}."
            ),
            "allowed_outputs": allowed_outputs
        }), 400

    output_path = temp_dir / f"{input_path.stem}{output_format}"
    result = toolkit.document_converter.convert(
        input_file=input_path,
        output_format=output_format,
        output_file=output_path,
        debug=debug_mode
    )

    debug_entry = {
        "conversionId": conversion_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sourceFile": safe_name,
        "sourceFormat": input_path.suffix.lower(),
        "documentType": effective_type,
        "outputProfile": output_profile,
        "outputFormat": output_format,
        "durationMs": round((time.perf_counter() - started) * 1000, 2),
        "success": bool(result.get("success")),
        "message": result.get("message", ""),
        "error": result.get("error"),
        "allowedOutputs": allowed_outputs
    }
    if result.get("debug"):
        debug_entry["converter"] = result["debug"]
    _store_debug_entry(debug_entry)

    if not result.get("success"):
        return jsonify({**result, "conversionId": conversion_id}), 400

    @after_this_request
    def cleanup(_response):
        for path in temp_dir.glob("*"):
            try:
                path.unlink()
            except OSError:
                pass
        try:
            temp_dir.rmdir()
        except OSError:
            pass
        return _response

    response = send_file(
        result["output_file"],
        as_attachment=True,
        download_name=Path(result["output_file"]).name
    )
    response.headers["X-Conversion-Id"] = conversion_id
    response.headers["X-Document-Type"] = effective_type
    response.headers["X-Output-Profile"] = output_profile
    return response


def _parse_data(text: str, data_format: str):
    clean = (text or "").strip()
    if data_format == "json":
        return json.loads(clean or "[]")

    if data_format == "ndjson":
        if not clean:
            return []
        return [json.loads(line) for line in clean.splitlines() if line.strip()]

    if data_format == "csv":
        if not clean:
            return []
        reader = csv.DictReader(io.StringIO(clean))
        return list(reader)

    if data_format == "keyvalue":
        data = {}
        for line in clean.splitlines():
            item = line.strip()
            if not item or item.startswith("#") or "=" not in item:
                continue
            key, value = item.split("=", 1)
            data[key.strip()] = value.strip()
        return data

    raise ValueError(f"Unsupported format: {data_format}")


def _stringify_data(payload, data_format: str) -> str:
    if data_format == "json":
        return json.dumps(payload, indent=2)

    if data_format == "ndjson":
        rows = payload if isinstance(payload, list) else [payload]
        return "\n".join(json.dumps(row) for row in rows)

    if data_format == "csv":
        rows = payload if isinstance(payload, list) else [payload]
        if not rows:
            return ""
        headers = sorted({key for row in rows for key in row.keys()})
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
        return stream.getvalue().strip()

    if data_format == "keyvalue":
        row = payload[0] if isinstance(payload, list) and payload else payload
        if not isinstance(row, dict):
            return ""
        return "\n".join(f"{key}={value}" for key, value in row.items())

    raise ValueError(f"Unsupported format: {data_format}")


def _normalize_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "active"}
    return bool(value)


def _load_snapshots():
    if not DATA_STORE_FILE.exists():
        return []
    try:
        return json.loads(DATA_STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_snapshots(snapshots):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_STORE_FILE.write_text(json.dumps(snapshots, indent=2), encoding="utf-8")


def _load_stored_documents():
    if not DOCUMENT_STORE_INDEX.exists():
        return []
    try:
        return json.loads(DOCUMENT_STORE_INDEX.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_stored_documents(items):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCUMENT_STORE_DIR.mkdir(parents=True, exist_ok=True)
    DOCUMENT_STORE_INDEX.write_text(json.dumps(items, indent=2), encoding="utf-8")


def _snapshot_summary(snapshot):
    payload = snapshot.get("payload", {})
    return {
        "id": snapshot.get("id"),
        "name": snapshot.get("name", ""),
        "createdAt": snapshot.get("createdAt"),
        "inputFormat": payload.get("inputFormat", ""),
        "outputFormat": payload.get("outputFormat", ""),
        "inputVersion": payload.get("inputVersion", ""),
        "outputVersion": payload.get("outputVersion", "")
    }


def _to_canonical(record, version: str):
    if version == "v1":
        return {
            "firstName": record.get("first_name", ""),
            "lastName": record.get("last_name", ""),
            "email": record.get("email", ""),
            "createdAt": record.get("created_at", ""),
            "active": _normalize_bool(record.get("active", False))
        }

    if version == "v2":
        full_name = str(record.get("fullName", "")).strip()
        parts = full_name.split()
        first = parts[0] if parts else ""
        last = " ".join(parts[1:]) if len(parts) > 1 else ""
        return {
            "firstName": first,
            "lastName": last,
            "email": record.get("emailAddress", ""),
            "createdAt": record.get("createdAt", ""),
            "active": _normalize_bool(record.get("status", False))
        }

    if version == "v3":
        name = record.get("name", {}) or {}
        contact = record.get("contact", {}) or {}
        meta = record.get("meta", {}) or {}
        return {
            "firstName": name.get("first", ""),
            "lastName": name.get("last", ""),
            "email": contact.get("email", ""),
            "createdAt": meta.get("createdAt", ""),
            "active": _normalize_bool(meta.get("active", False))
        }

    raise ValueError(f"Unsupported version: {version}")


def _from_canonical(model, version: str):
    if version == "v1":
        return {
            "first_name": model["firstName"],
            "last_name": model["lastName"],
            "email": model["email"],
            "created_at": model["createdAt"],
            "active": model["active"]
        }

    if version == "v2":
        return {
            "fullName": f"{model['firstName']} {model['lastName']}".strip(),
            "emailAddress": model["email"],
            "createdAt": model["createdAt"],
            "status": "active" if model["active"] else "inactive"
        }

    if version == "v3":
        return {
            "name": {"first": model["firstName"], "last": model["lastName"]},
            "contact": {"email": model["email"]},
            "meta": {"createdAt": model["createdAt"], "active": model["active"]}
        }

    raise ValueError(f"Unsupported version: {version}")


@app.post("/api/data/convert")
def convert_data():
    payload = request.get_json(silent=True) or {}
    required = ("inputText", "inputFormat", "outputFormat", "inputVersion", "outputVersion")
    missing = [name for name in required if name not in payload]
    if missing:
        return jsonify({"message": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        parsed = _parse_data(payload["inputText"], payload["inputFormat"])
        rows = parsed if isinstance(parsed, list) else [parsed]
        mapped = [_from_canonical(_to_canonical(row, payload["inputVersion"]), payload["outputVersion"]) for row in rows]
        if payload["outputFormat"] == "keyvalue":
            output_payload = mapped[0] if mapped else {}
        else:
            output_payload = mapped

        return jsonify({
            "outputText": _stringify_data(output_payload, payload["outputFormat"]),
            "stats": {
                "records": len(mapped),
                "source": f"{payload['inputFormat']}/{payload['inputVersion']}",
                "target": f"{payload['outputFormat']}/{payload['outputVersion']}"
            }
        })
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


@app.get("/api/data/store")
def list_data_snapshots():
    snapshots = _load_snapshots()
    snapshots.sort(key=lambda item: item.get("createdAt", ""), reverse=True)
    return jsonify({"items": [_snapshot_summary(item) for item in snapshots]})


@app.post("/api/data/store")
def create_data_snapshot():
    payload = request.get_json(silent=True) or {}
    required = ("inputText", "inputFormat", "outputFormat", "inputVersion", "outputVersion")
    missing = [name for name in required if name not in payload]
    if missing:
        return jsonify({"message": f"Missing fields: {', '.join(missing)}"}), 400

    snapshot = {
        "id": uuid.uuid4().hex,
        "name": str(payload.get("name", "")).strip() or "Untitled snapshot",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "inputText": payload.get("inputText", ""),
            "outputText": payload.get("outputText", ""),
            "inputFormat": payload.get("inputFormat", ""),
            "outputFormat": payload.get("outputFormat", ""),
            "inputVersion": payload.get("inputVersion", ""),
            "outputVersion": payload.get("outputVersion", "")
        }
    }

    snapshots = _load_snapshots()
    snapshots.append(snapshot)
    _save_snapshots(snapshots)
    return jsonify({"item": _snapshot_summary(snapshot)}), 201


@app.get("/api/data/store/<snapshot_id>")
def get_data_snapshot(snapshot_id: str):
    snapshots = _load_snapshots()
    item = next((entry for entry in snapshots if entry.get("id") == snapshot_id), None)
    if not item:
        return jsonify({"message": "Snapshot not found"}), 404
    return jsonify({"item": item})


@app.delete("/api/data/store/<snapshot_id>")
def delete_data_snapshot(snapshot_id: str):
    snapshots = _load_snapshots()
    filtered = [entry for entry in snapshots if entry.get("id") != snapshot_id]
    if len(filtered) == len(snapshots):
        return jsonify({"message": "Snapshot not found"}), 404
    _save_snapshots(filtered)
    return jsonify({"success": True})


@app.get("/<path:resource>")
def static_files(resource: str):
    return send_from_directory(BASE_DIR, resource)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
