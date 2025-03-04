import streamlit as st
import time
from typing import List, Dict, Optional

def show_validation_step(step: str, status: str, details: str = ""):
    """Display a single validation step with animation."""
    if status == "running":
        spinner = st.spinner(f"{step}...")
        with spinner:
            time.sleep(0.5)  # Simulate processing time
    elif status == "complete":
        st.success(f"{step} ✓")
        if details:
            st.write(details)
    elif status == "error":
        st.error(f"{step} ✗")
        if details:
            st.error(details)

def validation_progress_tracker(steps: Optional[List[Dict[str, str]]] = None):
    """
    Display an animated progress tracker for ZKP validation and blockchain confirmation.

    Args:
        steps: List of dictionaries containing step information:
              [{"name": "Step Name", "status": "running/complete/error", "details": "Optional details"}]
    """
    if not steps:
        steps = [
            {"name": "Generating Data Hash", "status": "running"},
            {"name": "Creating Zero-Knowledge Proof", "status": "pending"},
            {"name": "Validating Proof", "status": "pending"},
            {"name": "Storing on Blockchain", "status": "pending"},
            {"name": "Confirming Transaction", "status": "pending"}
        ]

    st.markdown("""
        <style>
        .validation-step {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            background-color: #f0f2f6;
        }
        .step-complete {
            background-color: #e6ffe6;
        }
        .step-error {
            background-color: #ffe6e6;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.subheader("Validation Progress")
        progress_bar = st.progress(0)

        for idx, step in enumerate(steps):
            progress = (idx + 1) / len(steps)
            with st.container():
                show_validation_step(
                    step["name"],
                    step["status"],
                    step.get("details", "")
                )
            progress_bar.progress(progress)

            if step["status"] == "error":
                break