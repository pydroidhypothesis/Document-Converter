#!/usr/bin/env python3
"""Web server for browser-based conversion."""

import csv
import io
import json
import os
import tempfile
import uuid
import time
import threading
import shutil
import secrets
import importlib
import importlib.metadata
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory, after_this_request, render_template
from werkzeug.utils import secure_filename

from document_converter import ConversionToolkit
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import DecodedStreamObject, NameObject


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
WEB_TEMPLATES_DIR = WEB_DIR / "templates"
WEB_STATIC_DIR = WEB_DIR / "static"
STORAGE_CONFIG_FILE = BASE_DIR / "config" / "storage_config.json"
ADMIN_CONFIG_FILE = BASE_DIR / "config" / "admin_config.json"
APP_STARTED_AT = datetime.now(timezone.utc)


def _resolve_path(path_str: str, default: Path) -> Path:
    if not path_str:
        return default
    raw = Path(path_str).expanduser()
    return raw if raw.is_absolute() else (BASE_DIR / raw).resolve()


def _load_storage_config():
    defaults = {
        "data_dir": "data",
        "snapshots_file": "data/snapshots.json",
        "documents_dir": "data/documents",
        "documents_index_file": "data/documents.json",
        "analytics_file": "data/analytics_events.csv"
    }
    if not STORAGE_CONFIG_FILE.exists():
        return defaults

    try:
        payload = json.loads(STORAGE_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return defaults

    if not isinstance(payload, dict):
        return defaults

    storage = payload.get("storage", payload)
    if not isinstance(storage, dict):
        return defaults

    merged = defaults.copy()
    for key in defaults:
        value = storage.get(key)
        if isinstance(value, str) and value.strip():
            merged[key] = value.strip()
    return merged


def _load_admin_token():
    env_token = (os.environ.get("DOC_CONVERT_ADMIN_TOKEN") or "").strip()
    if env_token:
        return env_token

    if not ADMIN_CONFIG_FILE.exists():
        return ""

    try:
        payload = json.loads(ADMIN_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return ""

    if not isinstance(payload, dict):
        return ""

    token = payload.get("admin_token") or payload.get("token") or ""
    return token.strip() if isinstance(token, str) else ""


_storage = _load_storage_config()
ADMIN_TOKEN = _load_admin_token()
DATA_DIR = _resolve_path(_storage["data_dir"], BASE_DIR / "data")
DATA_STORE_FILE = _resolve_path(_storage["snapshots_file"], DATA_DIR / "snapshots.json")
DOCUMENT_STORE_DIR = _resolve_path(_storage["documents_dir"], DATA_DIR / "documents")
DOCUMENT_STORE_INDEX = _resolve_path(_storage["documents_index_file"], DATA_DIR / "documents.json")
ANALYTICS_STORE_FILE = _resolve_path(_storage["analytics_file"], DATA_DIR / "analytics_events.csv")
ANALYTICS_LOCK = threading.Lock()
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
CONVERSION_JOBS = {}
CONVERSION_JOBS_LOCK = threading.Lock()
app = Flask(
    __name__,
    template_folder=str(WEB_TEMPLATES_DIR),
    static_folder=str(WEB_STATIC_DIR),
    static_url_path="/static"
)
toolkit = ConversionToolkit()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/formats/document")
def document_formats():
    return jsonify(toolkit.document_converter.supported_formats)


@app.get("/api/formats/libreoffice")
def libreoffice_formats():
    lo_input = [".odt", ".ott", ".sxw", ".fodt", ".ods", ".ots", ".fods", ".odp", ".otp", ".fodp"]
    lo_output = [".pdf", ".odt", ".ods", ".odp", ".epub", ".html", ".txt", ".xml", ".csv"]
    return jsonify({
        "input": lo_input,
        "output": lo_output
    })


@app.get("/api/formats/audio")
def audio_formats():
    return jsonify(toolkit.audio_converter.supported_formats)


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


def _update_job(job_id: str, **updates):
    with CONVERSION_JOBS_LOCK:
        job = CONVERSION_JOBS.get(job_id)
        if not job:
            return
        job.update(updates)
        job["updatedAt"] = datetime.now(timezone.utc).isoformat()


def _get_job(job_id: str):
    with CONVERSION_JOBS_LOCK:
        return CONVERSION_JOBS.get(job_id)


def _pop_job(job_id: str):
    with CONVERSION_JOBS_LOCK:
        return CONVERSION_JOBS.pop(job_id, None)


def _run_document_conversion_job(job_id: str):
    job = _get_job(job_id)
    if not job:
        return

    input_path = Path(job["inputPath"])
    output_path = Path(job["outputPath"])
    temp_dir = Path(job["tempDir"])
    output_format = job["outputFormat"]
    selected_type = job["documentType"]
    output_profile = job["outputProfile"]
    debug_mode = bool(job.get("debug"))
    safe_name = job["safeName"]
    started = time.perf_counter()
    conversion_id = uuid.uuid4().hex

    try:
        _update_job(job_id, status="running", progress=15, stage="validating", message="Validating input file...")
        detected_type = _detect_document_type(input_path.suffix.lower())
        if not detected_type:
            _update_job(
                job_id,
                status="failed",
                progress=100,
                stage="failed",
                message=f"Unsupported source file type: {input_path.suffix.lower() or '(none)'}"
            )
            return

        if selected_type != "auto" and selected_type not in OUTPUT_PROFILE_FORMATS:
            _update_job(
                job_id,
                status="failed",
                progress=100,
                stage="failed",
                message=f"Unsupported document type: {selected_type}"
            )
            return

        if output_profile not in {"legacy", "modern"}:
            _update_job(
                job_id,
                status="failed",
                progress=100,
                stage="failed",
                message=f"Unsupported output profile: {output_profile}"
            )
            return

        effective_type = detected_type if selected_type == "auto" else selected_type
        if selected_type != "auto" and selected_type != detected_type:
            _update_job(
                job_id,
                status="failed",
                progress=100,
                stage="failed",
                message=f"File type mismatch. Uploaded file is {detected_type}, selected type is {selected_type}."
            )
            return

        allowed_outputs = _get_output_formats_for(effective_type, output_profile)
        if output_format not in allowed_outputs:
            _update_job(
                job_id,
                status="failed",
                progress=100,
                stage="failed",
                message=f"Output format {output_format} is not allowed for type {effective_type} with profile {output_profile}."
            )
            return

        _update_job(job_id, progress=60, stage="converting", message="Converting with LibreOffice...")
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
            _update_job(
                job_id,
                status="failed",
                progress=100,
                stage="failed",
                message=result.get("message", "Document conversion failed"),
                error=result.get("error"),
                conversionId=conversion_id
            )
            return

        _update_job(job_id, progress=90, stage="finalizing", message="Preparing download...")
        if not output_path.exists():
            _update_job(
                job_id,
                status="failed",
                progress=100,
                stage="failed",
                message="Converted file is missing"
            )
            return

        _update_job(
            job_id,
            status="completed",
            progress=100,
            stage="completed",
            message="Conversion complete",
            conversionId=conversion_id,
            outputFile=str(output_path),
            outputFilename=output_path.name
        )
    except Exception as exc:
        _update_job(
            job_id,
            status="failed",
            progress=100,
            stage="failed",
            message=f"Conversion failed: {exc}",
            error=str(exc)
        )


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


@app.get("/api/document/store/tree")
def get_stored_document_tree():
    DOCUMENT_STORE_DIR.mkdir(parents=True, exist_ok=True)
    payload = _build_storage_tree(DOCUMENT_STORE_DIR.resolve(), request.args.get("path") or "")
    if payload.get("error"):
        return jsonify({"message": payload["error"]}), payload.get("status", 400)
    return jsonify(payload)


@app.get("/api/storage/config")
def get_storage_config():
    roots = _get_storage_roots()
    return jsonify({
        "storage": {
            "dataDir": str(DATA_DIR.resolve()),
            "snapshotsFile": str(DATA_STORE_FILE.resolve()),
            "documentsDir": str(DOCUMENT_STORE_DIR.resolve()),
            "documentsIndexFile": str(DOCUMENT_STORE_INDEX.resolve())
        },
        "roots": [
            {"key": "documents", "label": "Documents", "path": str(roots["documents"]), "exists": roots["documents"].exists()},
            {"key": "data", "label": "Data", "path": str(roots["data"]), "exists": roots["data"].exists()},
            {"key": "snapshots", "label": "Snapshots Folder", "path": str(roots["snapshots"]), "exists": roots["snapshots"].exists()}
        ]
    })


@app.get("/api/storage/tree")
def get_storage_tree():
    roots = _get_storage_roots()
    root_key = (request.args.get("root") or "documents").strip().lower()
    if root_key not in roots:
        return jsonify({"message": "Invalid storage root"}), 400

    root = roots[root_key]
    root.mkdir(parents=True, exist_ok=True)
    payload = _build_storage_tree(root, request.args.get("path") or "")
    if payload.get("error"):
        return jsonify({"message": payload["error"]}), payload.get("status", 400)

    payload["rootKey"] = root_key
    return jsonify(payload)


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


@app.post("/api/document/convert/start")
def start_document_conversion():
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

    job_id = uuid.uuid4().hex
    temp_dir = Path(tempfile.mkdtemp(prefix=f"docconvert_job_{job_id[:8]}_"))
    input_path = temp_dir / safe_name
    source.save(input_path)
    output_path = temp_dir / f"{input_path.stem}{output_format}"

    now = datetime.now(timezone.utc).isoformat()
    with CONVERSION_JOBS_LOCK:
        CONVERSION_JOBS[job_id] = {
            "jobId": job_id,
            "status": "queued",
            "progress": 5,
            "stage": "queued",
            "message": "Job queued",
            "createdAt": now,
            "updatedAt": now,
            "tempDir": str(temp_dir),
            "inputPath": str(input_path),
            "outputPath": str(output_path),
            "safeName": safe_name,
            "outputFormat": output_format,
            "documentType": selected_type,
            "outputProfile": output_profile,
            "debug": debug_mode,
            "outputFile": None,
            "outputFilename": None,
            "conversionId": None,
            "error": None
        }

    thread = threading.Thread(target=_run_document_conversion_job, args=(job_id,), daemon=True)
    thread.start()

    return jsonify({
        "jobId": job_id,
        "status": "queued",
        "progress": 5,
        "stage": "queued",
        "message": "Job started"
    }), 202


@app.get("/api/document/convert/status/<job_id>")
def get_document_conversion_status(job_id: str):
    job = _get_job(job_id)
    if not job:
        return jsonify({"message": "Job not found"}), 404

    return jsonify({
        "jobId": job["jobId"],
        "status": job["status"],
        "progress": job.get("progress", 0),
        "stage": job.get("stage", ""),
        "message": job.get("message", ""),
        "outputFilename": job.get("outputFilename"),
        "conversionId": job.get("conversionId"),
        "error": job.get("error")
    })


@app.get("/api/document/convert/download/<job_id>")
def download_document_conversion(job_id: str):
    job = _get_job(job_id)
    if not job:
        return jsonify({"message": "Job not found"}), 404

    if job.get("status") != "completed":
        return jsonify({"message": "Job is not completed yet"}), 409

    output_file = job.get("outputFile")
    if not output_file:
        return jsonify({"message": "No output file available"}), 404

    path = Path(output_file)
    if not path.exists():
        return jsonify({"message": "Converted file missing on disk"}), 404

    @after_this_request
    def cleanup(_response):
        temp_dir = Path(job.get("tempDir", ""))
        for item in temp_dir.glob("*"):
            try:
                item.unlink()
            except OSError:
                pass
        try:
            temp_dir.rmdir()
        except OSError:
            pass
        _pop_job(job_id)
        return _response

    return send_file(
        path,
        as_attachment=True,
        download_name=job.get("outputFilename") or path.name
    )


@app.post("/api/audio/convert")
def convert_audio():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "Missing uploaded file"}), 400

    source = request.files["file"]
    output_format = (request.form.get("output_format") or "").strip().lower()
    bitrate = (request.form.get("bitrate") or "").strip()

    if not output_format:
        return jsonify({"success": False, "message": "Missing output format"}), 400

    if not output_format.startswith("."):
        output_format = f".{output_format}"

    if source.filename is None or source.filename.strip() == "":
        return jsonify({"success": False, "message": "Invalid source filename"}), 400

    safe_name = secure_filename(source.filename)
    if not safe_name:
        safe_name = "audio"

    temp_dir = Path(tempfile.mkdtemp(prefix="audioconvert_"))
    input_path = temp_dir / safe_name
    source.save(input_path)
    output_path = temp_dir / f"{input_path.stem}{output_format}"

    kwargs = {"output_file": output_path}
    if bitrate:
        kwargs["bitrate"] = bitrate

    try:
        result = toolkit.audio_converter.convert(
            input_file=input_path,
            output_format=output_format,
            **kwargs
        )
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

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


@app.post("/api/pdf/process")
def process_pdf():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "Missing uploaded PDF file"}), 400

    source = request.files["file"]
    mode = (request.form.get("mode") or "compress").strip().lower()
    if mode not in {"compress", "decompress"}:
        return jsonify({"success": False, "message": "Invalid mode. Use compress or decompress."}), 400

    if source.filename is None or source.filename.strip() == "":
        return jsonify({"success": False, "message": "Invalid source filename"}), 400

    safe_name = secure_filename(source.filename)
    if not safe_name:
        safe_name = "document.pdf"
    if not safe_name.lower().endswith(".pdf"):
        return jsonify({"success": False, "message": "Only PDF files are supported for this operation."}), 400

    temp_dir = Path(tempfile.mkdtemp(prefix="pdfprocess_"))
    input_path = temp_dir / safe_name
    output_suffix = "_compressed.pdf" if mode == "compress" else "_decompressed.pdf"
    output_path = temp_dir / f"{Path(safe_name).stem}{output_suffix}"
    source.save(input_path)

    try:
        reader = PdfReader(str(input_path))
        writer = PdfWriter()

        for page in reader.pages:
            page_ref = page
            if mode == "compress":
                try:
                    page_ref.compress_content_streams()
                except Exception:
                    pass
            else:
                try:
                    contents = page_ref.get_contents()
                    if contents:
                        decoded = DecodedStreamObject()
                        decoded.set_data(contents.get_data())
                        page_ref[NameObject("/Contents")] = decoded
                except Exception:
                    pass

            writer.add_page(page_ref)

        if reader.metadata:
            writer.add_metadata({})  # Remove metadata for smaller, cleaner output.

        with output_path.open("wb") as handle:
            writer.write(handle)
    except Exception as exc:
        for path in temp_dir.glob("*"):
            try:
                path.unlink()
            except OSError:
                pass
        try:
            temp_dir.rmdir()
        except OSError:
            pass
        return jsonify({"success": False, "message": f"PDF {mode} failed: {exc}"}), 400

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
        str(output_path),
        as_attachment=True,
        download_name=output_path.name,
        mimetype="application/pdf"
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


def _bytes_to_readable(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def _require_admin():
    if not ADMIN_TOKEN:
        return jsonify({"message": "Admin token is not configured on server."}), 503

    provided = (request.headers.get("X-Admin-Token") or "").strip()
    if not provided or not secrets.compare_digest(provided, ADMIN_TOKEN):
        return jsonify({"message": "Admin access denied."}), 403
    return None


def _check_dependency(module_name: str, package_name: str):
    try:
        importlib.import_module(module_name)
        try:
            version = importlib.metadata.version(package_name)
        except Exception:
            version = "unknown"
        return {
            "name": package_name,
            "module": module_name,
            "installed": True,
            "version": version
        }
    except Exception as exc:
        return {
            "name": package_name,
            "module": module_name,
            "installed": False,
            "version": None,
            "error": str(exc)
        }


def _job_stats():
    with CONVERSION_JOBS_LOCK:
        jobs = list(CONVERSION_JOBS.values())
    counts = {"queued": 0, "running": 0, "completed": 0, "failed": 0, "other": 0}
    for job in jobs:
        status = (job.get("status") or "").lower()
        if status in counts:
            counts[status] += 1
        else:
            counts["other"] += 1
    counts["total"] = len(jobs)
    return counts


def _request_client_ip():
    forwarded = (request.headers.get("X-Forwarded-For") or "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    return (request.remote_addr or "").strip()


def _ensure_analytics_store():
    headers = [
        "timestamp",
        "eventType",
        "ip",
        "userAgent",
        "source",
        "documentType",
        "inputFormat",
        "outputFormat",
        "outputProfile",
        "success",
        "durationMs",
        "notes"
    ]
    try:
        ANALYTICS_STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not ANALYTICS_STORE_FILE.exists():
            with ANALYTICS_STORE_FILE.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=headers)
                writer.writeheader()
    except Exception:
        return


def _track_analytics_event(event_type: str, **fields):
    _ensure_analytics_store()
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "eventType": event_type,
        "ip": fields.get("ip", ""),
        "userAgent": fields.get("userAgent", ""),
        "source": fields.get("source", ""),
        "documentType": fields.get("documentType", ""),
        "inputFormat": fields.get("inputFormat", ""),
        "outputFormat": fields.get("outputFormat", ""),
        "outputProfile": fields.get("outputProfile", ""),
        "success": str(bool(fields.get("success", False))).lower(),
        "durationMs": str(fields.get("durationMs", "")),
        "notes": fields.get("notes", "")
    }

    try:
        with ANALYTICS_LOCK:
            with ANALYTICS_STORE_FILE.open("a", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
                writer.writerow(row)
    except Exception:
        return


def _load_analytics_rows():
    _ensure_analytics_store()
    if not ANALYTICS_STORE_FILE.exists():
        return []
    try:
        with ANALYTICS_STORE_FILE.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def _summarize_analytics(rows):
    visits = 0
    conversions = 0
    success_count = 0
    by_doc_type = {}
    by_output_format = {}
    by_output_profile = {}
    by_source = {}

    for row in rows:
        event_type = (row.get("eventType") or "").strip()
        if event_type == "visit":
            visits += 1
            continue

        if event_type.startswith("document_conversion"):
            conversions += 1
            source = (row.get("source") or "").strip() or "unknown"
            by_source[source] = by_source.get(source, 0) + 1

            if (row.get("success") or "").strip().lower() == "true":
                success_count += 1

            doc_type = (row.get("documentType") or "").strip() or "unknown"
            by_doc_type[doc_type] = by_doc_type.get(doc_type, 0) + 1

            output_format = (row.get("outputFormat") or "").strip() or "unknown"
            by_output_format[output_format] = by_output_format.get(output_format, 0) + 1

            profile = (row.get("outputProfile") or "").strip() or "unknown"
            by_output_profile[profile] = by_output_profile.get(profile, 0) + 1

    return {
        "totals": {
            "visits": visits,
            "documentConversions": conversions,
            "successfulDocumentConversions": success_count
        },
        "breakdown": {
            "byDocumentType": by_doc_type,
            "byOutputFormat": by_output_format,
            "byOutputProfile": by_output_profile,
            "bySource": by_source
        }
    }


def _get_storage_roots():
    roots = {
        "documents": DOCUMENT_STORE_DIR.resolve(),
        "data": DATA_DIR.resolve(),
        "snapshots": DATA_STORE_FILE.resolve().parent
    }
    return roots


def _build_storage_tree(root: Path, requested: str):
    root = root.resolve()
    requested = (requested or "").strip()

    target = (root / requested).resolve() if requested else root
    if target != root and root not in target.parents:
        return {"error": "Invalid path", "status": 400}
    if not target.exists() or not target.is_dir():
        return {"error": "Folder not found", "status": 404}

    current_rel = "" if target == root else str(target.relative_to(root))
    if target == root:
        parent_rel = None
    else:
        parent = target.parent
        parent_rel = "" if parent == root else str(parent.relative_to(root))

    entries = []
    children = sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
    for child in children:
        try:
            stats = child.stat()
        except OSError:
            continue

        is_dir = child.is_dir()
        rel = str(child.relative_to(root))
        folder_items = None
        if is_dir:
            try:
                folder_items = sum(1 for _ in child.iterdir())
            except OSError:
                folder_items = 0
        entry = {
            "name": child.name,
            "path": rel,
            "type": "folder" if is_dir else "file",
            "sizeBytes": None if is_dir else int(stats.st_size),
            "sizeReadable": f"{folder_items} items" if is_dir else _bytes_to_readable(int(stats.st_size)),
            "modifiedAt": datetime.fromtimestamp(stats.st_mtime, timezone.utc).isoformat()
        }
        entries.append(entry)

    return {
        "root": str(root),
        "currentPath": current_rel,
        "parentPath": parent_rel,
        "entries": entries
    }


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
