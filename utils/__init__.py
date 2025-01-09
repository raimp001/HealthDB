"""
Utils package initialization file.
Contains shared utilities for the research platform.
"""
import pandas as pd
import json
from typing import Dict, Any, List, Optional
import io

def validate_data(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate research data format and content."""
    try:
        # Basic validation checks
        if not isinstance(data, dict):
            return False, "Data must be a dictionary"

        # Check for required fields
        required_fields = ["title", "description", "data_type"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"

        # Validate data content based on type
        if data.get("data_type") == "numeric":
            if not isinstance(data.get("values"), (list, pd.Series)):
                return False, "Numeric data must be a list or series"

        elif data.get("data_type") == "categorical":
            if not isinstance(data.get("categories"), (list, pd.Series)):
                return False, "Categories must be a list or series"

        return True, "Data validation successful"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def generate_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate metadata for research data."""
    metadata = {
        "created_at": pd.Timestamp.now().isoformat(),
        "data_type": data.get("data_type"),
        "record_count": len(data.get("values", [])) if "values" in data else 0,
        "fields": list(data.keys()),
    }

    if "categories" in data:
        metadata["unique_categories"] = len(set(data["categories"]))

    return metadata

def prepare_data_export(data: List[Dict[str, Any]], format: str = "json") -> Any:
    """Prepare research data for export in specified format."""
    try:
        if format.lower() == "json":
            return json.dumps(data, indent=2)

        elif format.lower() == "csv":
            df = pd.DataFrame(data)
            return df.to_csv(index=False)

        elif format.lower() == "excel":
            df = pd.DataFrame(data)
            output = io.BytesIO()
            df.to_excel(output, index=False)
            return output.getvalue()

        else:
            raise ValueError(f"Unsupported export format: {format}")

    except Exception as e:
        raise Exception(f"Error preparing data export: {str(e)}")