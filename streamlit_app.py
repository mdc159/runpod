"""Streamlit helper for managing RunPod network volume files via the S3-compatible API."""
from __future__ import annotations

import io
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional

import boto3
import streamlit as st
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

try:
    from upload_large_file import LargeMultipartUploader
except ModuleNotFoundError:  # pragma: no cover - defensive guard for renamed file
    LargeMultipartUploader = None  # type: ignore[assignment]

load_dotenv()

REGION_TO_ENDPOINT = {
    "eu-cz-1": "https://s3api-eu-cz-1.runpod.io",
    "eu-ro-1": "https://s3api-eu-ro-1.runpod.io",
    "eur-is-1": "https://s3api-eur-is-1.runpod.io",
    "us-ca-2": "https://s3api-us-ca-2.runpod.io",
    "us-ks-2": "https://s3api-us-ks-2.runpod.io",
}

SUPPORTED_REGIONS = tuple(sorted(REGION_TO_ENDPOINT))


@dataclass
class ConnectionSettings:
    """Container for the current RunPod S3 connection."""

    access_key: str
    secret_key: str
    region: str
    endpoint: str
    bucket: str

    @property
    def endpoint_hint(self) -> str:
        return REGION_TO_ENDPOINT.get(self.region, self.endpoint)


def load_default_settings() -> ConnectionSettings:
    """Read defaults from the environment (populated via .env)."""

    region = os.getenv("RUNPOD_REGION", "us-ca-2").lower()
    endpoint = os.getenv("RUNPOD_ENDPOINT", REGION_TO_ENDPOINT.get(region, ""))
    return ConnectionSettings(
        access_key=os.getenv("AWS_ACCESS_KEY_ID", ""),
        secret_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        region=region,
        endpoint=endpoint,
        bucket=os.getenv("RUNPOD_BUCKET", ""),
    )


@st.cache_resource(show_spinner=False)
def get_s3_client(access_key: str, secret_key: str, region: str, endpoint: str):
    """Create (and cache) a boto3 S3 client for the provided credentials."""

    session = boto3.session.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    return session.client("s3", endpoint_url=endpoint or None)


def render_sidebar() -> Optional[ConnectionSettings]:
    """Render the sidebar connection form and return the active settings."""

    st.sidebar.header("RunPod connection")
    defaults = load_default_settings()
    existing = st.session_state.get("connection")

    with st.sidebar.form("connection_form", clear_on_submit=False):
        access_key = st.text_input(
            "Access key ID",
            value=(existing or defaults).access_key,
            help="RunPod S3 access key (user_*)",
        )
        secret_key = st.text_input(
            "Secret access key",
            value=(existing or defaults).secret_key,
            type="password",
            help="RunPod S3 secret (rps_*)",
        )
        region = st.selectbox(
            "Datacenter region",
            SUPPORTED_REGIONS,
            index=max(0, SUPPORTED_REGIONS.index((existing or defaults).region)
                      if (existing or defaults).region in SUPPORTED_REGIONS else 0),
            help="Only supported datacenters expose the S3-compatible API.",
        )
        suggested_endpoint = REGION_TO_ENDPOINT.get(region, (existing or defaults).endpoint)
        endpoint = st.text_input(
            "S3 endpoint URL",
            value=suggested_endpoint,
            help="Override only if RunPod issues a custom endpoint URL.",
        )
        bucket = st.text_input(
            "Network volume ID",
            value=(existing or defaults).bucket,
            help="Shown as the bucket name when using the RunPod S3 API.",
        )
        submitted = st.form_submit_button("Connect")

    if submitted:
        missing = [field for field, value in {
            "Access key": access_key,
            "Secret": secret_key,
            "Bucket": bucket,
        }.items() if not value]
        if missing:
            st.sidebar.error(f"Missing fields: {', '.join(missing)}")
            return None
        st.session_state["connection"] = ConnectionSettings(
            access_key=access_key.strip(),
            secret_key=secret_key.strip(),
            region=region,
            endpoint=endpoint.strip(),
            bucket=bucket.strip(),
        )
        st.sidebar.success("Connected!", icon="✅")

    return st.session_state.get("connection")


def ensure_connection(settings: Optional[ConnectionSettings]) -> bool:
    if settings is None:
        st.info("Configure your RunPod credentials in the sidebar to begin.")
        return False
    return True


def normalize_key(prefix: str, filename: str) -> str:
    sanitized = prefix.strip().lstrip("/")
    base = Path(filename).name
    return f"{sanitized}/{base}" if sanitized else base


def list_objects(client, bucket: str, prefix: str, recursive: bool, max_items: int) -> List[dict]:
    paginator = client.get_paginator("list_objects_v2")
    kwargs = {"Bucket": bucket, "Prefix": prefix}
    if not recursive:
        kwargs["Delimiter"] = "/"

    objects: List[dict] = []
    for page in paginator.paginate(**kwargs, PaginationConfig={"MaxItems": max_items}):
        for obj in page.get("Contents", []):
            objects.append({
                "Key": obj["Key"],
                "Size": obj["Size"],
                "LastModified": obj["LastModified"],
            })
        if len(objects) >= max_items:
            break
    return objects


def show_error(exc: Exception):
    if isinstance(exc, ClientError):
        response: dict[str, Any] = getattr(exc, "response", {}) or {}
        error = response.get("Error", {})
        code = error.get("Code")
        msg = error.get("Message")
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        st.error(f"AWS error {status or ''} ({code}): {msg}")
    else:
        st.error(str(exc))


def browse_tab(client, settings: ConnectionSettings):
    with st.form("browse_form"):
        prefix = st.text_input("Prefix filter", value="")
        recursive = st.checkbox("Include subdirectories", value=False)
        max_items = st.slider("Max objects", min_value=100, max_value=5000, value=1000, step=100)
        submitted = st.form_submit_button("List objects")

    if submitted:
        try:
            with st.spinner("Listing objects..."):
                objects = list_objects(client, settings.bucket, prefix, recursive, max_items)
            st.session_state["last_listing"] = objects
        except (BotoCoreError, ClientError) as exc:
            show_error(exc)
            return

    objects = st.session_state.get("last_listing", [])
    if not objects:
        st.info("Run a listing to populate this table.")
        return

    st.success(f"Showing {len(objects)} object(s) from {settings.bucket}")
    st.dataframe(objects, use_container_width=True)


def upload_small_files(client, settings: ConnectionSettings, files: Iterable[io.BytesIO], prefix: str):
    for file_obj in files:
        filename = getattr(file_obj, "name", "uploaded_file")
        key = normalize_key(prefix, filename)
        data = io.BytesIO(file_obj.read())
        total_bytes = len(data.getbuffer())
        data.seek(0)

        progress = st.progress(0.0, text=f"Uploading {key}")
        uploaded = 0

        def callback(chunk: int):
            nonlocal uploaded
            uploaded += chunk
            progress.progress(min(uploaded / total_bytes, 1.0), text=f"Uploading {key}")

        try:
            client.upload_fileobj(data, settings.bucket, key, Callback=callback)
            progress.progress(1.0, text=f"Uploaded {key}")
            st.success(f"Uploaded {key} ({total_bytes / (1024 ** 2):.2f} MB)")
        except (BotoCoreError, ClientError) as exc:
            progress.empty()
            show_error(exc)


def upload_large_file(settings: ConnectionSettings, local_path: str, remote_key: str, chunk_size: int):
    if LargeMultipartUploader is None:
        st.error("upload_large_file.py is missing; cannot perform multipart uploads.")
        return

    uploader = LargeMultipartUploader(
        file_path=local_path,
        bucket=settings.bucket,
        key=remote_key,
        region=settings.region,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
        endpoint=settings.endpoint,
        part_size=chunk_size,
    )
    with st.spinner(f"Uploading {local_path}..."):
        uploader.upload()
    st.success(f"Completed multipart upload for {remote_key}")


def upload_tab(client, settings: ConnectionSettings):
    st.subheader("Upload files")
    st.write("Use the quick uploader for browser-selected files or switch to local-path multipart mode for files >10GB.")

    with st.form("upload_form"):
        files = st.file_uploader("Select files", accept_multiple_files=True)
        prefix = st.text_input("Remote folder (optional)")
        use_multipart = st.checkbox("Use local path + multipart helper", value=False)
        local_path = st.text_input("Local file path", placeholder="/path/to/large/file", disabled=not use_multipart)
        remote_name = st.text_input("Remote filename (leave blank to keep original)")
        chunk_size_mb = st.slider("Multipart chunk size (MB)", min_value=5, max_value=500, value=50, disabled=not use_multipart)
        submit = st.form_submit_button("Start upload")

    if not submit:
        return

    if use_multipart:
        if not local_path:
            st.error("Provide a local path for multipart uploads.")
            return
        upload_target = remote_name or Path(local_path).name
        key = normalize_key(prefix, upload_target)
        try:
            upload_large_file(settings, local_path, key, chunk_size_mb * 1024 * 1024)
        except Exception as exc:  # noqa: BLE001 - surface all errors to the UI
            show_error(exc)
        return

    if not files:
        st.error("Select at least one file for the standard uploader.")
        return

    upload_small_files(client, settings, files, prefix)


def download_tab(client, settings: ConnectionSettings):
    st.subheader("Download files")
    cached_objects = st.session_state.get("last_listing", [])
    options = [obj["Key"] for obj in cached_objects]

    key = st.selectbox(
        "Choose file from last listing",
        options=options if options else [""],
        index=0,
        disabled=not options,
    )
    manual_key = st.text_input("Or enter a specific key")
    destination = st.text_input("Local path", value=str(Path.cwd() / (Path(manual_key or key or "download.bin").name)))
    download_button = st.button("Download")

    if not download_button:
        return

    target_key = manual_key or key
    if not target_key:
        st.error("Specify an object key to download.")
        return

    try:
        head = client.head_object(Bucket=settings.bucket, Key=target_key)
        total_bytes = head.get("ContentLength", 0)
    except (BotoCoreError, ClientError) as exc:
        show_error(exc)
        return

    progress = st.progress(0.0, text=f"Downloading {target_key}")
    downloaded = 0

    def callback(chunk: int):
        nonlocal downloaded
        downloaded += chunk
        progress.progress(min(downloaded / total_bytes if total_bytes else 0, 1.0), text=f"Downloading {target_key}")

    try:
        client.download_file(settings.bucket, target_key, destination, Callback=callback)
        progress.progress(1.0, text=f"Downloaded {target_key}")
        st.success(f"Saved to {destination}")
    except (BotoCoreError, ClientError) as exc:
        progress.empty()
        show_error(exc)


def main():
    st.set_page_config(page_title="RunPod Volume Transfer", layout="wide")
    st.title("RunPod Volume Transfer Console")
    st.caption("List, upload, and download files via the RunPod S3-compatible API.")

    settings = render_sidebar()
    if not ensure_connection(settings):
        return

    assert settings is not None

    try:
        client = get_s3_client(
            settings.access_key,
            settings.secret_key,
            settings.region,
            settings.endpoint or settings.endpoint_hint,
        )
    except Exception as exc:  # noqa: BLE001
        show_error(exc)
        return

    browse, upload, download = st.tabs(["Browse", "Upload", "Download"])
    with browse:
        browse_tab(client, settings)
    with upload:
        upload_tab(client, settings)
    with download:
        download_tab(client, settings)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
