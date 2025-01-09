import streamlit as st
import openai
from typing import Dict, Any, Optional
import json

class ResearchInsightsSidebar:
    def __init__(self):
        self.client = openai.OpenAI()
        
    def generate_insights(self, context: Dict[str, Any]) -> str:
        """Generate research insights based on current context."""
        try:
            # Prepare context for AI analysis
            prompt = f"""
            Based on the following research context, provide valuable insights and suggestions:
            
            Current View: {context.get('current_view', 'Not specified')}
            Project: {context.get('project_name', 'Not specified')}
            Research Area: {context.get('research_area', 'Not specified')}
            
            Please provide:
            1. Related research directions
            2. Potential collaboration opportunities
            3. Methodology suggestions
            4. Research gap analysis
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a research advisor helping scientists identify valuable insights and opportunities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating insights: {str(e)}"
            
    def render(self, context: Optional[Dict[str, Any]] = None):
        """Render the insights sidebar with Aleo design system."""
        with st.sidebar:
            st.markdown("""
                <style>
                .insights-container {
                    background-color: #F5F5F5;  /* Ivory */
                    padding: 1rem;
                    border-radius: 8px;
                    border: 1px solid rgba(18, 18, 18, 0.1);
                    margin-bottom: 1rem;
                }
                .insights-header {
                    color: #121212;  /* Coal */
                    font-family: 'Inter', sans-serif;
                    font-weight: 600;
                    margin-bottom: 1rem;
                }
                .insight-item {
                    background-color: #E3E3E3;  /* Stone */
                    padding: 0.75rem;
                    border-radius: 4px;
                    margin-bottom: 0.5rem;
                    border-left: 3px solid #C4F652;  /* Lime */
                }
                </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="insights-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="insights-header">Research Insights</h3>', unsafe_allow_html=True)
            
            if context:
                with st.spinner("Generating research insights..."):
                    insights = self.generate_insights(context)
                    
                    # Split insights into sections
                    sections = insights.split('\n\n')
                    for section in sections:
                        if section.strip():
                            st.markdown(f'<div class="insight-item">{section}</div>', 
                                      unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

def get_insights_sidebar() -> ResearchInsightsSidebar:
    """Get or create insights sidebar instance."""
    if 'insights_sidebar' not in st.session_state:
        st.session_state.insights_sidebar = ResearchInsightsSidebar()
    return st.session_state.insights_sidebar
