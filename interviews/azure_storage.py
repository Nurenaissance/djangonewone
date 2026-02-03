"""
Azure Blob Storage utility for uploading interview audio files
"""
import os
import logging
from datetime import datetime
from typing import Optional, BinaryIO
from django.conf import settings
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import AzureError

logger = logging.getLogger(__name__)


class AzureStorageClient:
    """
    Client for uploading files to Azure Blob Storage
    """

    def __init__(self):
        """Initialize the Azure Blob Storage client"""
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER
        self.account_name = settings.AZURE_STORAGE_ACCOUNT_NAME

        if not self.connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is not configured")

        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            self.container_client = self.blob_service_client.get_container_client(
                self.container_name
            )

            # Ensure container exists
            if not self.container_client.exists():
                logger.warning(f"Container {self.container_name} does not exist. Creating it...")
                self.container_client.create_container()
                logger.info(f"Container {self.container_name} created successfully")

        except AzureError as e:
            logger.error(f"Failed to initialize Azure Blob Storage client: {e}")
            raise

    def upload_audio_file(
        self,
        file_data: BinaryIO,
        candidate_name: str,
        interview_type: str,
        part_name: str,
        file_extension: str = "wav"
    ) -> Optional[str]:
        """
        Upload an audio file to Azure Blob Storage with structured path

        Args:
            file_data: Binary file data (file object or bytes)
            candidate_name: Name of the candidate (used in path)
            interview_type: 'vidushi' or 'maan_vidushi'
            part_name: e.g., 'calibration', 'part1', 'part2'
            file_extension: File extension (default: 'wav')

        Returns:
            Public URL of the uploaded file, or None if upload failed

        Structure:
            interviews/{interview_type}/{candidate_name_sanitized}/{timestamp}_{part_name}.{ext}

        Example:
            interviews/vidushi/john_doe/20260203_143022_calibration.wav
        """
        try:
            # Sanitize candidate name for use in path (remove special chars, spaces to underscores)
            candidate_name_clean = self._sanitize_filename(candidate_name)

            # Generate timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Construct blob path
            blob_path = f"interviews/{interview_type}/{candidate_name_clean}/{timestamp}_{part_name}.{file_extension}"

            logger.info(f"Uploading audio file to: {blob_path}")

            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )

            # Set content type for audio files
            content_settings = ContentSettings(
                content_type='audio/wav' if file_extension == 'wav' else 'audio/mpeg'
            )

            # Upload the file
            # If file_data is a file object, read it; if it's bytes, use directly
            if hasattr(file_data, 'read'):
                file_data.seek(0)  # Ensure we're at the beginning
                blob_client.upload_blob(
                    file_data,
                    overwrite=True,
                    content_settings=content_settings
                )
            else:
                blob_client.upload_blob(
                    file_data,
                    overwrite=True,
                    content_settings=content_settings
                )

            # Generate the public URL
            public_url = blob_client.url
            logger.info(f"File uploaded successfully: {public_url}")

            return public_url

        except AzureError as e:
            logger.error(f"Azure Blob Storage error during upload: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {e}")
            return None

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for use in Azure Blob Storage paths

        Args:
            filename: Original filename

        Returns:
            Sanitized filename with only alphanumeric chars, underscores, and hyphens
        """
        import re

        # Convert to lowercase
        filename = filename.lower()

        # Replace spaces with underscores
        filename = filename.replace(" ", "_")

        # Remove all non-alphanumeric characters except underscores and hyphens
        filename = re.sub(r'[^a-z0-9_\-]', '', filename)

        # Limit length to 50 characters
        filename = filename[:50]

        return filename

    def delete_file(self, blob_url: str) -> bool:
        """
        Delete a file from Azure Blob Storage

        Args:
            blob_url: Full URL of the blob to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Extract blob path from URL
            # URL format: https://{account}.blob.core.windows.net/{container}/{blob_path}
            blob_path = blob_url.split(f"{self.container_name}/")[-1]

            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )

            blob_client.delete_blob()
            logger.info(f"File deleted successfully: {blob_path}")
            return True

        except AzureError as e:
            logger.error(f"Failed to delete file from Azure Blob Storage: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during file deletion: {e}")
            return False

    def file_exists(self, blob_url: str) -> bool:
        """
        Check if a file exists in Azure Blob Storage

        Args:
            blob_url: Full URL of the blob to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            blob_path = blob_url.split(f"{self.container_name}/")[-1]

            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )

            return blob_client.exists()

        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False


# Singleton instance
_azure_storage_client = None


def get_azure_storage_client() -> AzureStorageClient:
    """
    Get or create the singleton Azure Storage client instance

    Returns:
        AzureStorageClient instance
    """
    global _azure_storage_client

    if _azure_storage_client is None:
        _azure_storage_client = AzureStorageClient()

    return _azure_storage_client
