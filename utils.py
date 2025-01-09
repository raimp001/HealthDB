import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

def validate_data(df):
    """Validate uploaded data for common issues."""
    validation_results = {
        'missing_values': df.isnull().sum().to_dict(),
        'duplicate_rows': df.duplicated().sum(),
        'column_types': df.dtypes.astype(str).to_dict()
    }
    return validation_results

def create_summary_visualization(df):
    """Create summary visualizations for the dataset."""
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    
    if len(numeric_cols) > 0:
        fig = go.Figure()
        for col in numeric_cols:
            fig.add_trace(go.Box(y=df[col], name=col))
        fig.update_layout(title="Numerical Data Distribution")
        return fig
    return None

def prepare_data_export(data, format_type):
    """Prepare data for export in various formats."""
    if format_type == 'csv':
        return data.to_csv(index=False)
    elif format_type == 'json':
        return data.to_json(orient='records')
    elif format_type == 'excel':
        return data.to_excel(index=False)
    return None

def generate_metadata(df):
    """Generate metadata for uploaded dataset."""
    metadata = {
        'num_rows': len(df),
        'num_columns': len(df.columns),
        'column_names': list(df.columns),
        'data_types': df.dtypes.astype(str).to_dict(),
        'missing_values_summary': df.isnull().sum().to_dict()
    }
    return json.dumps(metadata)
