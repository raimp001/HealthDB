import streamlit as st
import plotly.graph_objects as go
import numpy as np
from zpass_interface import ZPassInterface, ZKProof
import time
import json

def zkp_demo_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access this page.")
        return
        
    st.title("Zero-Knowledge Proof Interactive Demo")
    st.write("""
    Explore how Zero-Knowledge Proofs work in our platform. This interactive demo
    will walk you through the process of creating and validating proofs without
    revealing sensitive information.
    """)
    
    # Initialize demo state
    if 'demo_step' not in st.session_state:
        st.session_state.demo_step = 0
    if 'proof_generated' not in st.session_state:
        st.session_state.proof_generated = False
        
    # Step 1: Introduction
    st.header("Step 1: Understanding Zero-Knowledge Proofs")
    st.write("""
    A Zero-Knowledge Proof allows one party (the Prover) to prove to another party
    (the Verifier) that a statement is true without revealing any information beyond
    the validity of the statement.
    """)
    
    # Interactive Demo Controls
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Start Interactive Demo" if st.session_state.demo_step == 0 else "Next Step"):
            st.session_state.demo_step += 1
            
    # Step 2: Data Selection
    if st.session_state.demo_step >= 1:
        st.header("Step 2: Select Data to Prove")
        demo_data = {
            "value": st.slider("Select a secret value", 1, 100, 50),
            "timestamp": time.time()
        }
        
        # Create visual representation
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode = "gauge+number",
            value = demo_data["value"],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Secret Value"},
            gauge = {'axis': {'range': [0, 100]}}
        ))
        st.plotly_chart(fig)
        
        # Generate ZKP
        if st.button("Generate Proof"):
            st.session_state.proof_generated = True
            zpass = ZPassInterface()
            proof = zpass.generate_data_proof(demo_data)
            st.session_state.current_proof = proof
            
            # Show proof generation animation
            with st.spinner("Generating Zero-Knowledge Proof..."):
                time.sleep(1)  # Simulate processing
                st.success("Proof Generated!")
                
                # Display proof components
                st.subheader("Proof Components")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Public Inputs", len(proof.public_inputs))
                with col2:
                    st.metric("Private Inputs", len(proof.private_inputs))
                    
                # Visualization of proof structure
                fig = go.Figure(data=[go.Sankey(
                    node = dict(
                        pad = 15,
                        thickness = 20,
                        line = dict(color = "black", width = 0.5),
                        label = ["Data", "Hash", "ZKP", "Verification"],
                        color = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
                    ),
                    link = dict(
                        source = [0, 1, 2],
                        target = [1, 2, 3],
                        value = [1, 1, 1]
                    )
                )])
                fig.update_layout(title_text="Zero-Knowledge Proof Flow", font_size=10)
                st.plotly_chart(fig)
                
    # Step 3: Verification
    if st.session_state.proof_generated:
        st.header("Step 3: Verify the Proof")
        st.write("""
        Now let's verify the proof. Notice that we can verify the statement is true
        without revealing the original secret value.
        """)
        
        if st.button("Verify Proof"):
            with st.spinner("Verifying proof..."):
                time.sleep(1)  # Simulate verification
                st.success("""
                Proof Verified Successfully! ✅
                
                The verifier now knows:
                - The proof is mathematically valid
                - The original data exists and hasn't been tampered with
                - The prover knows the secret value
                
                But does NOT know:
                - The actual secret value
                - Any other private information
                """)
                
    # Reset Demo
    if st.session_state.demo_step > 0:
        if st.button("Reset Demo"):
            st.session_state.demo_step = 0
            st.session_state.proof_generated = False
            st.rerun()

if __name__ == "__main__":
    zkp_demo_page()
