"""Storage module for landing Parquet datasets and manifest metadata into S3 / LocalStack / Local Data Lake."""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import pandas as pd

logger = logging.getLogger("TransitPulse.Ingestion.Storage")


class StorageManager:
    """Handles landing datasets as compressed Parquet files and generating JSON execution manifests."""

    def __init__(
        self,
        s3_endpoint: Optional[str] = None,
        bucket_name: str = "transitpulse",
        local_base_dir: str = "./data/raw_landing"
    ):
        self.bucket_name = os.getenv("S3_BUCKET", bucket_name)
        self.local_base_dir = Path(local_base_dir)
        self.s3_endpoint = s3_endpoint or os.getenv("S3_ENDPOINT", "http://localhost:4566")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID", "test")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
        self.aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

        self.s3_client = self._init_s3_client()

    def _init_s3_client(self):
        """Initialize S3 client for MinIO or LocalStack simulation."""
        try:
            client = boto3.client(
                "s3",
                endpoint_url=self.s3_endpoint,
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            return client
        except Exception as e:
            logger.warning(f"Could not initialize S3 client ({e}). Falling back to local storage only.")
            return None

    def save_parquet(
        self,
        df: pd.DataFrame,
        category: str,  # 'transit' or 'weather'
        dataset_name: str,
        execution_date: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Save DataFrame as snappy-compressed Parquet locally and upload to S3.
        Returns (local_file_path, s3_uri).
        """
        if execution_date is None:
            execution_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 1. Local Landing Path Setup
        target_dir = self.local_base_dir / category / dataset_name / execution_date
        target_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{dataset_name}_{timestamp_str}.parquet"
        local_path = target_dir / filename

        # 2. Save locally as Parquet
        df.to_parquet(local_path, index=False, compression="snappy")
        logger.info(f"Saved local Parquet: {local_path} ({len(df)} rows)")

        # 3. S3 Upload Logic
        s3_key = f"bronze/{category}/{dataset_name}/{execution_date}/{filename}"
        s3_uri = f"s3://{self.bucket_name}/{s3_key}"

        if self.s3_client:
            try:
                # Ensure bucket exists
                self._ensure_bucket_exists()
                self.s3_client.upload_file(str(local_path), self.bucket_name, s3_key)
                logger.info(f"Uploaded to S3: {s3_uri}")
            except (BotoCoreError, ClientError) as e:
                logger.warning(f"S3 upload failed for {s3_uri}: {e}. Local file preserved.")
                s3_uri = None

        return str(local_path), s3_uri

    def _ensure_bucket_exists(self):
        """Create bucket in S3/LocalStack if it doesn't already exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created S3 bucket: {self.bucket_name}")
            except Exception as e:
                logger.debug(f"Bucket check/create note: {e}")

    def create_manifest(
        self,
        category: str,
        dataset_name: str,
        metrics: Dict[str, Any],
        local_file_path: str,
        s3_uri: Optional[str] = None,
        execution_date: Optional[str] = None
    ) -> str:
        """Create JSON execution manifest file detailing ingestion run metrics."""
        if execution_date is None:
            execution_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        manifest_dir = self.local_base_dir / category / dataset_name / execution_date
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / f"manifest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

        manifest_data = {
            "dataset": dataset_name,
            "category": category,
            "execution_date": execution_date,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "local_file_path": local_file_path,
            "s3_uri": s3_uri,
            "raw_row_count": metrics.get("raw_count", 0),
            "clean_row_count": metrics.get("clean_count", 0),
            "dropped_nulls": metrics.get("dropped_nulls", 0),
            "duplicates_removed": metrics.get("duplicates_removed", 0),
            "status": metrics.get("status", "UNKNOWN"),
            "null_summary": metrics.get("null_summary", {})
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        logger.info(f"Manifest created at: {manifest_path}")
        return str(manifest_path)
