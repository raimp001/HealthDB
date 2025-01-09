import streamlit as st
import openai
import os
from scholarly import scholarly, ProxyGenerator
from typing import Dict, List, Optional
import json

class LiteratureReviewAssistant:
    def __init__(self):
        self.client = openai.OpenAI()
        
    def analyze_paper(self, paper_data: Dict) -> Dict:
        """Analyze a research paper using OpenAI API."""
        try:
            # Prepare the analysis prompt
            prompt = f"""
            Analyze the following research paper and provide:
            1. A comprehensive summary
            2. Key findings and contributions
            3. Research methodology
            4. Limitations and future work
            5. Related research areas
            
            Title: {paper_data.get('title', '')}
            Authors: {', '.join(paper_data.get('authors', []))}
            Abstract: {paper_data.get('abstract', '')}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a research assistant helping with literature review."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            analysis = response.choices[0].message.content
            return {
                'analysis': analysis,
                'paper_info': paper_data
            }
        except Exception as e:
            st.error(f"Error analyzing paper: {str(e)}")
            return None
            
    def suggest_related_papers(self, paper_data: Dict) -> List[Dict]:
        """Find related papers based on the current paper."""
        try:
            # Configure proxy for scholarly
            pg = ProxyGenerator()
            pg.FreeProxies()
            scholarly.use_proxy(pg)
            
            # Search for related papers
            search_query = f"{paper_data['title']} {' '.join(paper_data['authors'][:1])}"
            search_results = scholarly.search_pubs(search_query)
            related_papers = []
            
            # Get first 5 related papers
            for _ in range(5):
                try:
                    paper = next(search_results)
                    related_papers.append({
                        'title': paper.bib.get('title'),
                        'authors': paper.bib.get('author', '').split(' and '),
                        'year': paper.bib.get('year'),
                        'abstract': paper.bib.get('abstract', '')
                    })
                except StopIteration:
                    break
                    
            return related_papers
        except Exception as e:
            st.error(f"Error finding related papers: {str(e)}")
            return []

def literature_review_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to use the literature review assistant.")
        return

    st.title("AI-Powered Literature Review Assistant")
    st.write("""
    Get in-depth analysis of research papers using AI. This tool helps you:
    - Analyze papers and extract key insights
    - Find related research
    - Generate comprehensive summaries
    - Identify research gaps and future directions
    """)
    
    # Initialize the assistant
    assistant = LiteratureReviewAssistant()
    
    # Paper search
    search_query = st.text_input("Enter paper title, DOI, or URL")
    
    if search_query:
        with st.spinner("Searching and analyzing paper..."):
            # Search for paper using scholarly
            pg = ProxyGenerator()
            pg.FreeProxies()
            scholarly.use_proxy(pg)
            
            try:
                search_results = scholarly.search_pubs(search_query)
                paper = next(search_results)
                
                paper_data = {
                    'title': paper.bib.get('title'),
                    'authors': paper.bib.get('author', '').split(' and '),
                    'year': paper.bib.get('year'),
                    'abstract': paper.bib.get('abstract', ''),
                    'url': paper.bib.get('url', '')
                }
                
                # Display paper details
                st.subheader("Paper Details")
                st.write(f"**Title:** {paper_data['title']}")
                st.write(f"**Authors:** {', '.join(paper_data['authors'])}")
                st.write(f"**Year:** {paper_data['year']}")
                
                # AI Analysis
                if st.button("Analyze Paper"):
                    with st.spinner("Performing AI analysis..."):
                        analysis_result = assistant.analyze_paper(paper_data)
                        
                        if analysis_result:
                            st.subheader("AI Analysis")
                            st.markdown(analysis_result['analysis'])
                            
                            # Find related papers
                            st.subheader("Related Papers")
                            with st.spinner("Finding related papers..."):
                                related_papers = assistant.suggest_related_papers(paper_data)
                                
                                for idx, related in enumerate(related_papers, 1):
                                    with st.expander(f"{idx}. {related['title']}"):
                                        st.write(f"**Authors:** {', '.join(related['authors'])}")
                                        st.write(f"**Year:** {related['year']}")
                                        st.write(f"**Abstract:** {related['abstract']}")
                
            except Exception as e:
                st.error(f"Error searching for paper: {str(e)}")

if __name__ == "__main__":
    literature_review_page()
