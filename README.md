# RunPod Streamlit Transfer Console

A local Streamlit application that lists, uploads, and downloads files in a RunPod network volume via the S3-compatible API. It wraps the official [`upload_large_file.py`](upload_large_file.py:1) helper for resilient multipart uploads and exposes a friendlier UI for daily workflows.

## Prerequisites

1. **Python 3.11+**
2. **uv** for dependency management (per repo guidelines)
3. RunPod S3 credentials (access key, secret, network volume ID, and datacenter endpoint)

## Setup

1. Copy the provided example environment file and populate it with your RunPod secrets:
   ```bash
   cp .env.example .env
   # edit .env with your values
   ```

2. Install dependencies with `uv`:
   ```bash
   uv pip install -r requirements.txt
   ```

3. Launch the Streamlit UI:
   ```bash
   streamlit run streamlit_app.py
   ```

4. In the sidebar, confirm the pre-populated credentials (sourced from `.env`) and click **Connect**. The main tabs will unlock once a client is created.

## Features

| Tab | Capabilities |
| --- | ------------ |
| **Browse** | Paginated listings with prefix filters, optional recursion, and cached results for quick reuse. |
| **Upload** | Single drag-and-drop surface that auto-routes each file: inline uploads for small items, multipart streaming (via [`LargeMultipartUploader.upload()`](upload_large_file.py:379)) for large selections. |
| **Download** | One-click downloads for any key returned by the last listing or a manual object path, with progress indicators and destination overrides. |

The app surfaces RunPod-specific HTTP errors (507 insufficient storage, 524 proxy timeouts, etc.) described in [`docs/S3-compatible-API.md`](docs/S3-compatible-API.md:170-228) and automatically invalidates cached listings after successful uploads.

## Testing checklist

1. **Connectivity** – Use the Browse tab to list a small prefix and confirm the bucket/endpoint pairing is correct.
2. **Standard upload** – Drag a small (<200 MB) file into the Upload tab and verify it appears in Browse after refreshing.
3. **Multipart upload** – Drag a multi-GB file; the app will automatically spool it to a temporary file and stream it via [`upload_large_file.py`](upload_large_file.py:379-475).
4. **Download** – Select any listed key, set a destination path, and confirm the file arrives locally.

For exceptionally large directories, refer back to RunPod's operational notes in [`docs/S3-compatible-API.md`](docs/S3-compatible-API.md:454-536) regarding pagination and timeout tuning.
