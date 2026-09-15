"""Data validation, cleaning, and metadata enrichment module for TransitPulse ingestion."""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

logger = logging.getLogger("TransitPulse.Ingestion.Validators")
logging.basicConfig(level=logging.INFO)


class SchemaValidationError(Exception):
    """Raised when a DataFrame fails schema validation."""
    pass


class DataValidator:
    """Validates, cleans, and enriches DataFrames during data ingestion."""

    @staticmethod
    def validate_required_columns(df: pd.DataFrame, required_columns: List[str], dataset_name: str) -> None:
        """Check that all required columns exist in the DataFrame."""
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            error_msg = f"[{dataset_name}] Missing required columns: {missing}. Present columns: {list(df.columns)}"
            logger.error(error_msg)
            raise SchemaValidationError(error_msg)
        logger.info(f"[{dataset_name}] Required columns validation passed: {required_columns}")

    @staticmethod
    def handle_missing_values(
        df: pd.DataFrame,
        critical_cols: List[str],
        default_fill_map: Optional[Dict[str, Any]] = None
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Handle null values:
        - Drops rows where any critical_cols are null.
        - Fills nulls in other columns according to default_fill_map.
        """
        initial_count = len(df)
        null_summary = df.isnull().sum().to_dict()

        # Drop rows missing critical identifiers
        cleaned_df = df.dropna(subset=critical_cols).copy()
        dropped_null_count = initial_count - len(cleaned_df)

        if dropped_null_count > 0:
            logger.warning(f"Dropped {dropped_null_count} rows due to nulls in critical columns: {critical_cols}")

        # Fill default values if provided
        if default_fill_map:
            for col, fill_val in default_fill_map.items():
                if col in cleaned_df.columns:
                    cleaned_df[col] = cleaned_df[col].fillna(fill_val)

        return cleaned_df, null_summary

    @staticmethod
    def remove_duplicates(df: pd.DataFrame, key_columns: List[str], dataset_name: str) -> Tuple[pd.DataFrame, int]:
        """Deduplicate records based on primary key columns, retaining the last observed record."""
        initial_count = len(df)
        deduped_df = df.drop_duplicates(subset=key_columns, keep="last").copy()
        duplicates_removed = initial_count - len(deduped_df)

        if duplicates_removed > 0:
            logger.info(f"[{dataset_name}] Removed {duplicates_removed} duplicate rows using key: {key_columns}")
        return deduped_df, duplicates_removed

    @staticmethod
    def enrich_metadata(df: pd.DataFrame, source_name: str, version: str = "1.0") -> pd.DataFrame:
        """Append standard ingestion metadata columns to the DataFrame."""
        enriched = df.copy()
        now_utc = datetime.now(timezone.utc).isoformat()
        enriched["_ingested_at"] = now_utc
        enriched["_source"] = source_name
        enriched["_version"] = version
        return enriched

    @classmethod
    def process_and_validate(
        cls,
        df: pd.DataFrame,
        dataset_name: str,
        required_columns: List[str],
        critical_columns: List[str],
        key_columns: List[str],
        default_fill_map: Optional[Dict[str, Any]] = None,
        source_name: str = "unknown"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Orchestrate full validation lifecycle:
        1. Validate schema columns
        2. Handle missing/null values
        3. Deduplicate
        4. Enrich metadata
        5. Return cleaned DataFrame and quality metrics
        """
        raw_count = len(df)
        if raw_count == 0:
            logger.warning(f"[{dataset_name}] Received empty DataFrame for validation.")
            metrics = {
                "dataset": dataset_name,
                "raw_count": 0,
                "clean_count": 0,
                "dropped_nulls": 0,
                "duplicates_removed": 0,
                "status": "EMPTY",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            return df, metrics

        # 1. Schema check
        cls.validate_required_columns(df, required_columns, dataset_name)

        # 2. Null handling
        df_cleaned, null_summary = cls.handle_missing_values(df, critical_columns, default_fill_map)
        dropped_nulls = raw_count - len(df_cleaned)

        # 3. Deduplication
        df_deduped, duplicates_removed = cls.remove_duplicates(df_cleaned, key_columns, dataset_name)

        # 4. Metadata enrichment
        df_final = cls.enrich_metadata(df_deduped, source_name=source_name)
        clean_count = len(df_final)

        metrics = {
            "dataset": dataset_name,
            "raw_count": raw_count,
            "clean_count": clean_count,
            "dropped_nulls": dropped_nulls,
            "duplicates_removed": duplicates_removed,
            "null_summary": null_summary,
            "status": "PASSED" if clean_count > 0 else "WARNING_ALL_DROPPED",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"[{dataset_name}] Validation Complete: Raw={raw_count}, Clean={clean_count}, DroppedNulls={dropped_nulls}, Deduped={duplicates_removed}")
        return df_final, metrics
