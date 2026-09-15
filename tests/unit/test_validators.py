"""Unit tests for DataValidator schema checking, null handling, and deduplication."""

import pytest
import pandas as pd
from ingestion.common.validators import DataValidator, SchemaValidationError


@pytest.mark.unit
def test_validate_required_columns_success():
    """Verify schema check succeeds when all columns are present."""
    df = pd.DataFrame({"col_a": [1, 2], "col_b": ["x", "y"]})
    DataValidator.validate_required_columns(df, ["col_a", "col_b"], "test_dataset")


@pytest.mark.unit
def test_validate_required_columns_failure():
    """Verify schema check raises SchemaValidationError when columns are missing."""
    df = pd.DataFrame({"col_a": [1, 2]})
    with pytest.raises(SchemaValidationError) as excinfo:
        DataValidator.validate_required_columns(df, ["col_a", "missing_col"], "test_dataset")
    assert "missing_col" in str(excinfo.value)


@pytest.mark.unit
def test_handle_missing_values():
    """Verify null handling drops critical nulls and fills defaults."""
    df = pd.DataFrame({
        "id": [1, 2, None, 4],
        "value": [10.0, None, 30.0, 40.0],
        "category": [None, "B", "C", "D"]
    })

    cleaned, summary = DataValidator.handle_missing_values(
        df=df,
        critical_cols=["id"],
        default_fill_map={"value": 0.0, "category": "UNKNOWN"}
    )

    assert len(cleaned) == 3
    assert None not in cleaned["id"].values
    assert cleaned.loc[cleaned["id"] == 2, "value"].values[0] == 0.0
    assert cleaned.loc[cleaned["id"] == 1, "category"].values[0] == "UNKNOWN"


@pytest.mark.unit
def test_remove_duplicates():
    """Verify deduplication removes duplicate keys while keeping the last record."""
    df = pd.DataFrame({
        "key": ["A", "B", "A"],
        "val": [1, 2, 99],
        "ts": [100, 200, 300]
    })

    deduped, removed_count = DataValidator.remove_duplicates(df, key_columns=["key"], dataset_name="test")
    assert removed_count == 1
    assert len(deduped) == 2
    assert deduped.loc[deduped["key"] == "A", "val"].values[0] == 99


@pytest.mark.unit
def test_enrich_metadata():
    """Verify metadata enrichment adds _ingested_at, _source, and _version."""
    df = pd.DataFrame({"id": [10, 20]})
    enriched = DataValidator.enrich_metadata(df, source_name="UNIT_TEST", version="2.0")

    assert "_ingested_at" in enriched.columns
    assert "_source" in enriched.columns
    assert "_version" in enriched.columns
    assert enriched["_source"].iloc[0] == "UNIT_TEST"
    assert enriched["_version"].iloc[0] == "2.0"
