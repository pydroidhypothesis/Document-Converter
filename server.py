#!/usr/bin/env python3
"""Web server for browser-based conversion."""

import csv
import io
import json
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory, after_this_request
from werkzeug.utils import secure_filename

from document_converter import ConversionToolkit


BASE_DIR = Path(__file__).resolve().parent
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


@app.post("/api/document/convert")
def convert_document():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "Missing uploaded file"}), 400

    source = request.files["file"]
    output_format = (request.form.get("output_format") or "").strip().lower()

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

    output_path = temp_dir / f"{input_path.stem}{output_format}"
    result = toolkit.document_converter.convert(
        input_file=input_path,
        output_format=output_format,
        output_file=output_path
    )

    if not result.get("success"):
        return jsonify(result), 400

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

    return send_file(
        result["output_file"],
        as_attachment=True,
        download_name=Path(result["output_file"]).name
    )


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


@app.get("/<path:resource>")
def static_files(resource: str):
    return send_from_directory(BASE_DIR, resource)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
