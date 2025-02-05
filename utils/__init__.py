"""
Utils package initialization file.
Contains shared utilities for the research platform.
"""
import pandas as pd
from datetime import datetime
import json

def validate_data(df: pd.DataFrame) -> tuple[bool, str]:
    """
    Validates uploaded data for basic requirements.

    Args:
        df: Pandas DataFrame to validate

    Returns:
        tuple: (is_valid: bool, message: str)
    """
    try:
        # Check if DataFrame is empty
        if df.empty:
            return False, "The uploaded file contains no data"

        # Check for minimum number of rows
        if len(df) < 1:
            return False, "The file must contain at least one row of data"

        # Check for minimum number of columns
        if len(df.columns) < 1:
            return False, "The file must contain at least one column"

        # Check for missing values
        missing_counts = df.isnull().sum()
        if missing_counts.any():
            columns_with_missing = missing_counts[missing_counts > 0].index.tolist()
            return False, f"Missing values found in columns: {', '.join(columns_with_missing)}"

        return True, "Data validation successful"

    except Exception as e:
        return False, f"Validation error: {str(e)}"

def generate_metadata(df: pd.DataFrame) -> dict:
    """
    Generates metadata for the uploaded dataset.

    Args:
        df: Pandas DataFrame to analyze

    Returns:
        dict: Metadata about the dataset
    """
    try:
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data_types": {col: str(df[col].dtype) for col in df.columns},
            "missing_values": {col: int(df[col].isnull().sum()) for col in df.columns},
            "memory_usage": {
                "total": f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB",
                "per_column": {col: f"{df[col].memory_usage(deep=True) / 1024 / 1024:.2f} MB" 
                              for col in df.columns}
            }
        }

        return metadata

    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }