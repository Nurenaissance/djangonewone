"""
Storage client for interview audio files.

Historically this hit Azure Blob (`pdffornurenai`). It now talks to MinIO via
S3 — same public class + function names so callers don't need to change. The
"azure" naming in the module / class is kept on purpose to avoid touching the
~dozen import sites; under the hood it's boto3-on-MinIO.
"""

import logging
import os
import re
from datetime import datetime
from typing import BinaryIO, Optional
from urllib.parse import urlparse

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


# Map of common audio/file extensions to correct MIME types.
#
# Historically this client hard-coded "audio/mpeg" as the default for anything
# that wasn't .wav — which silently broke playback for browser-recorded .webm
# files (every interview-dashboard audio link returned audio/mpeg, browsers
# tried to decode as MP3 and failed). The mapping below covers every audio
# format the browser MediaRecorder API can emit, plus the WhatsApp media
# extensions we see in inbound webhooks.
_AUDIO_MIME = {
    "wav": "audio/wav",
    "webm": "audio/webm",
    "ogg": "audio/ogg",
    "oga": "audio/ogg",
    "opus": "audio/ogg",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "mp4": "audio/mp4",
    "aac": "audio/aac",
    "amr": "audio/amr",
    "3gp": "audio/3gpp",
    "flac": "audio/flac",
}


def _audio_content_type(file_extension: str) -> str:
    """Resolve the right Content-Type for an audio upload from its extension.
    Falls back to audio/<ext> for unknown types so the file is at least
    served as audio (not mpeg)."""
    ext = (file_extension or "").lstrip(".").lower()
    return _AUDIO_MIME.get(ext, f"audio/{ext}" if ext else "application/octet-stream")


class AzureStorageClient:
    """S3 client for interview audio uploads. Name kept for call-site compat."""

    def __init__(self):
        self.endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
        self.bucket = os.getenv("S3_BUCKET", "nuren-media")
        self.public_url = os.getenv(
            "S3_PUBLIC_URL", "https://storage.nuren.ai/nuren-media"
        ).rstrip("/")
        access_key = os.getenv("S3_ACCESS_KEY")
        secret_key = os.getenv("S3_SECRET_KEY")

        if not access_key or not secret_key:
            raise ValueError(
                "S3_ACCESS_KEY / S3_SECRET_KEY are not configured. See /opt/nuren/.env."
            )

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=os.getenv("S3_REGION", "us-east-1"),
            # MinIO needs path-style (`endpoint/bucket/key`); vhost style would
            # require a wildcard cert + DNS.
            config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

        # Ensure bucket exists. MinIO returns 404 on HeadBucket if missing.
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ("404", "NoSuchBucket", "NotFound"):
                logger.warning("Bucket %s missing — creating", self.bucket)
                self.client.create_bucket(Bucket=self.bucket)
            else:
                logger.error("Bucket check failed: %s", e)
                raise

    def upload_audio_file(
        self,
        file_data: BinaryIO,
        candidate_name: str,
        interview_type: str,
        part_name: str,
        file_extension: str = "wav",
    ) -> Optional[str]:
        """Upload an audio file and return its public URL (or None on failure)."""
        try:
            candidate_name_clean = self._sanitize_filename(candidate_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = (
                f"interviews/{interview_type}/{candidate_name_clean}/"
                f"{timestamp}_{part_name}.{file_extension}"
            )

            content_type = _audio_content_type(file_extension)

            if hasattr(file_data, "read"):
                file_data.seek(0)
                body = file_data.read()
            else:
                body = file_data

            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
                ContentType=content_type,
            )

            url = f"{self.public_url}/{key}"
            logger.info("Uploaded %s -> %s", key, url)
            return url

        except ClientError as e:
            logger.error("S3 upload error: %s", e)
            return None
        except Exception as e:
            logger.exception("Unexpected upload error: %s", e)
            return None

    def upload_file(
        self,
        file_data: BinaryIO,
        prefix: str,
        original_filename: str,
        content_type: Optional[str] = None,
    ) -> Optional[str]:
        """Generic-purpose upload. Used by the /files/upload/ endpoint
        (which replaces the old frontend-direct-to-Azure SAS pattern).

        prefix:            logical folder under the bucket
                           (e.g. "flow_uploads/<tenant>/<user>")
        original_filename: client-side name; sanitised + timestamped to
                           guarantee key uniqueness even on collisions
        content_type:      passed through if provided; falls back to the
                           browser-sent MIME on the file_data object, then
                           to application/octet-stream

        Returns the public URL on success, None on failure.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            orig = (original_filename or "upload").strip()
            if "." in orig:
                base, _, ext = orig.rpartition(".")
            else:
                base, ext = orig, "bin"
            base_clean = self._sanitize_filename(base)
            ext_clean = re.sub(r"[^a-z0-9]", "", ext.lower())[:8] or "bin"
            prefix_clean = "/".join(
                self._sanitize_filename(p) for p in (prefix or "files").split("/") if p
            )
            key = f"{prefix_clean}/{timestamp}_{base_clean}.{ext_clean}"

            inferred_type = (
                content_type
                or getattr(file_data, "content_type", None)
                or "application/octet-stream"
            )

            if hasattr(file_data, "read"):
                file_data.seek(0)
                body = file_data.read()
            else:
                body = file_data

            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
                ContentType=inferred_type,
            )

            url = f"{self.public_url}/{key}"
            logger.info("Uploaded %s -> %s", key, url)
            return url

        except ClientError as e:
            logger.error("S3 upload error: %s", e)
            return None
        except Exception as e:
            logger.exception("Unexpected upload error: %s", e)
            return None

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        filename = (filename or "").lower().replace(" ", "_")
        filename = re.sub(r"[^a-z0-9_\-]", "", filename)
        return filename[:50]

    def _key_from_url(self, url: str) -> str:
        # Accept either the new MinIO URL or the legacy Azure URL — strip the
        # host + bucket/container prefix and return the remaining object key.
        path = urlparse(url).path.lstrip("/")
        # path is either "<bucket>/<key>" (MinIO path-style) or
        # "<container>/<key>" (legacy Azure). Drop the first segment.
        if "/" in path:
            _, _, key = path.partition("/")
            return key
        return path

    def delete_file(self, blob_url: str) -> bool:
        try:
            key = self._key_from_url(blob_url)
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            logger.error("Delete failed: %s", e)
            return False

    def file_exists(self, blob_url: str) -> bool:
        try:
            key = self._key_from_url(blob_url)
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ("404", "NoSuchKey", "NotFound"):
                return False
            logger.error("file_exists check failed: %s", e)
            return False


_azure_storage_client: Optional[AzureStorageClient] = None


def get_azure_storage_client() -> AzureStorageClient:
    """Singleton accessor — name kept for call-site compatibility."""
    global _azure_storage_client
    if _azure_storage_client is None:
        _azure_storage_client = AzureStorageClient()
    return _azure_storage_client
