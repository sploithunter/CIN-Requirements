from uuid import UUID, uuid4

import boto3
from botocore.config import Config

from app.core.config import get_settings

settings = get_settings()


class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version="s3v4"),
        )
        self.bucket_name = settings.s3_bucket_name

    async def upload_file(
        self,
        content: bytes,
        filename: str,
        content_type: str,
        session_id: UUID,
    ) -> tuple[str, str]:
        """
        Upload a file to S3/R2 storage.
        Returns: (storage_key, public_url)
        """
        # Generate unique storage key
        file_ext = filename.split(".")[-1] if "." in filename else ""
        unique_filename = f"{uuid4()}.{file_ext}" if file_ext else str(uuid4())
        storage_key = f"sessions/{session_id}/{unique_filename}"

        # Upload to S3
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=storage_key,
            Body=content,
            ContentType=content_type,
        )

        # Generate URL (for R2, this might be a custom domain)
        url = f"{settings.s3_endpoint_url}/{self.bucket_name}/{storage_key}"

        return storage_key, url

    async def delete_file(self, storage_key: str) -> None:
        """Delete a file from storage."""
        self.s3_client.delete_object(
            Bucket=self.bucket_name,
            Key=storage_key,
        )

    async def get_presigned_url(
        self,
        storage_key: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned URL for temporary access."""
        url = self.s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": storage_key,
            },
            ExpiresIn=expires_in,
        )
        return url

    async def download_file(self, storage_key: str) -> bytes:
        """Download a file from storage."""
        response = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=storage_key,
        )
        return response["Body"].read()
