"""
Utils package initialization file.
Contains shared utilities for the research platform.
"""
import pandas as pd
from datetime import datetime
import json
import io

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

def prepare_data_export(df: pd.DataFrame, format_type: str, include_metadata: bool = True):
    """
    Prepares data for export in various formats.

    Args:
        df: Pandas DataFrame to export
        format_type: Export format ('csv', 'json', 'excel')
        include_metadata: Whether to include metadata in the export

    Returns:
        File-like object or string with the exported data
    """
    try:
        metadata = generate_metadata(df) if include_metadata else None

        if format_type == 'csv':
            output = df.to_csv(index=False)
            if include_metadata:
                metadata_str = json.dumps(metadata, indent=2)
                # Fix: Create the replaced string separately first
                metadata_commented = metadata_str.replace("\n", "\n# ")
                output = f"# Metadata:\n# {metadata_commented}\n\n{output}"
            return output

        elif format_type == 'json':
            if include_metadata:
                data_dict = {
                    "metadata": metadata,
                    "data": json.loads(df.to_json(orient='records'))
                }
                return json.dumps(data_dict, indent=2)
            else:
                return df.to_json(orient='records')

        elif format_type == 'excel':
            buffer = io.BytesIO()
            writer = pd.ExcelWriter(buffer, engine='openpyxl')
            df.to_excel(writer, sheet_name='Data', index=False)

            if include_metadata:
                # Convert metadata to DataFrame for Excel sheet
                meta_items = []
                if metadata:  # Check if metadata is not None
                    for key, value in metadata.items():
                        if isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                meta_items.append({
                                    "Category": key,
                                    "Property": subkey,
                                    "Value": str(subvalue)
                                })
                        else:
                            meta_items.append({
                                "Category": "",
                                "Property": key,
                                "Value": str(value)
                            })
                    meta_df = pd.DataFrame(meta_items)
                    meta_df.to_excel(writer, sheet_name='Metadata', index=False)

            writer.close()
            buffer.seek(0)
            return buffer

        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    except Exception as e:
        raise Exception(f"Error preparing data export: {str(e)}")