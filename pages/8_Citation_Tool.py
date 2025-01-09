import streamlit as st
import scholarly
import json
from datetime import datetime
from pybtex.database import Entry, Person, BibliographyData
from scholarly import scholarly, ProxyGenerator

def format_apa_citation(paper_data):
    """Format citation in APA style."""
    try:
        authors = paper_data.get('authors', [])
        if len(authors) > 1:
            author_text = ", ".join(authors[:-1]) + f", & {authors[-1]}"
        else:
            author_text = authors[0] if authors else "Unknown Author"

        year = paper_data.get('year', 'n.d.')
        title = paper_data.get('title', '')
        journal = paper_data.get('journal', '')
        volume = paper_data.get('volume', '')
        issue = paper_data.get('number', '')
        pages = paper_data.get('pages', '')

        citation = f"{author_text} ({year}). {title}. "
        if journal:
            citation += f"{journal}"
            if volume:
                citation += f", {volume}"
                if issue:
                    citation += f"({issue})"
            if pages:
                citation += f", {pages}"
        citation += "."
        return citation
    except Exception as e:
        st.error(f"Error formatting APA citation: {str(e)}")
        return None

def format_mla_citation(paper_data):
    """Format citation in MLA style."""
    try:
        authors = paper_data.get('authors', [])
        if len(authors) > 2:
            author_text = f"{authors[0]} et al."
        elif len(authors) == 2:
            author_text = f"{authors[0]} and {authors[1]}"
        else:
            author_text = authors[0] if authors else "Unknown Author"

        title = paper_data.get('title', '')
        journal = paper_data.get('journal', '')
        volume = paper_data.get('volume', '')
        issue = paper_data.get('number', '')
        year = paper_data.get('year', '')
        pages = paper_data.get('pages', '')

        citation = f"{author_text}. \"{title}.\""
        if journal:
            citation += f" {journal}"
            if volume:
                citation += f", vol. {volume}"
                if issue:
                    citation += f", no. {issue}"
            if pages:
                citation += f", {pages}"
        if year:
            citation += f", {year}"
        citation += "."
        return citation
    except Exception as e:
        st.error(f"Error formatting MLA citation: {str(e)}")
        return None

def search_paper(query):
    """Search for paper using scholarly."""
    try:
        # Configure proxy generator for reliability
        pg = ProxyGenerator()
        pg.FreeProxies()
        scholarly.use_proxy(pg)
        
        # Search for the paper
        search_query = scholarly.search_pubs(query)
        paper = next(search_query)
        
        # Extract relevant information
        paper_data = {
            'title': paper.bib.get('title'),
            'authors': [author for author in paper.bib.get('author', '').split(' and ')],
            'year': paper.bib.get('year'),
            'journal': paper.bib.get('journal', ''),
            'volume': paper.bib.get('volume', ''),
            'number': paper.bib.get('number', ''),
            'pages': paper.bib.get('pages', ''),
            'url': paper.bib.get('url', ''),
            'abstract': paper.bib.get('abstract', '')
        }
        return paper_data
    except Exception as e:
        st.error(f"Error searching for paper: {str(e)}")
        return None

def citation_tool_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to use the citation tool.")
        return

    st.title("Academic Citation Tool")
    st.write("""
    Generate properly formatted citations for academic papers with just one click.
    Enter a paper title, DOI, or URL to get started.
    """)

    # Search input
    search_query = st.text_input("Enter paper title, DOI, or URL")
    
    if search_query:
        with st.spinner("Searching for paper..."):
            paper_data = search_paper(search_query)
            
            if paper_data:
                st.success("Paper found!")
                
                # Display paper details
                st.subheader("Paper Details")
                st.write(f"**Title:** {paper_data['title']}")
                st.write(f"**Authors:** {', '.join(paper_data['authors'])}")
                st.write(f"**Year:** {paper_data['year']}")
                st.write(f"**Journal:** {paper_data['journal']}")
                
                # Generate citations
                st.subheader("Citations")
                
                # APA format
                apa_citation = format_apa_citation(paper_data)
                if apa_citation:
                    st.write("**APA Format:**")
                    with st.container():
                        col1, col2 = st.columns([5,1])
                        with col1:
                            st.text_area("", apa_citation, height=100, key="apa", disabled=True)
                        with col2:
                            if st.button("Copy APA", key="copy_apa"):
                                st.write("Copied!")
                
                # MLA format
                mla_citation = format_mla_citation(paper_data)
                if mla_citation:
                    st.write("**MLA Format:**")
                    with st.container():
                        col1, col2 = st.columns([5,1])
                        with col1:
                            st.text_area("", mla_citation, height=100, key="mla", disabled=True)
                        with col2:
                            if st.button("Copy MLA", key="copy_mla"):
                                st.write("Copied!")
                
                # Export options
                st.subheader("Export Options")
                export_format = st.selectbox(
                    "Select export format",
                    ["BibTeX", "RIS", "EndNote"]
                )
                
                if st.button("Export Citation"):
                    # TODO: Implement export functionality
                    st.info("Export functionality coming soon!")

if __name__ == "__main__":
    citation_tool_page()
