import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import json

class GrobidPDFExtractor:
    def __init__(self, grobid_server="http://192.168.20.156:8070"):
        self.grobid_server = grobid_server
        self.session = requests.Session()
    
    def process_pdf(self, pdf_path):
        """
        Process PDF file with GROBID and extract structured information
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            dict: Extracted paper information
        """
        try:
            # Check if GROBID server is running
            self._check_server()
            
            # Process PDF with GROBID
            tei_xml = self._process_fulltext(pdf_path)
            
            # Parse XML and extract information
            extracted_info = self._parse_tei_xml(tei_xml)
            
            return extracted_info
            
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return None
    
    def _check_server(self):
        """Check if GROBID server is running"""
        try:
            response = self.session.get(f"{self.grobid_server}/api/isalive")
            if response.status_code != 200:
                raise Exception("GROBID server is not responding")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to GROBID server. Make sure it's running on localhost:8070")
    
    def _process_fulltext(self, pdf_path):
        """Send PDF to GROBID for full text processing"""
        url = f"{self.grobid_server}/api/processFulltextDocument"
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {'input': pdf_file}
            response = self.session.post(url, files=files)
        
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"GROBID processing failed with status {response.status_code}")
    
    def _parse_tei_xml(self, tei_xml):
        """Parse TEI XML and extract required information"""
        try:
            root = ET.fromstring(tei_xml)
            
            # Define namespace
            ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
            
            # Extract title
            title = self._extract_title(root, ns)
            
            # Extract authors
            authors = self._extract_authors(root, ns)
            
            # Extract abstract
            abstract = self._extract_abstract(root, ns)
            
            # Extract introduction
            introduction = self._extract_introduction(root, ns)
            
            return {
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'introduction': introduction
            }
            
        except ET.ParseError as e:
            print(f"XML parsing error: {str(e)}")
            return None
    
    def _extract_title(self, root, ns):
        """Extract paper title"""
        title_elem = root.find('.//tei:titleStmt/tei:title[@type="main"]', ns)
        if title_elem is not None:
            return self._clean_text(title_elem.text or "")
        
        # Fallback: try without type attribute
        title_elem = root.find('.//tei:titleStmt/tei:title', ns)
        if title_elem is not None:
            return self._clean_text(title_elem.text or "")
        
        return "Title not found"
    
    def _extract_authors(self, root, ns):
        """Extract author names"""
        authors = []
        
        # Find all author elements
        author_elems = root.findall('.//tei:sourceDesc//tei:author', ns)
        
        for author in author_elems:
            # Try to get full name
            persname = author.find('.//tei:persName', ns)
            if persname is not None:
                # Get forename and surname
                forename_elem = persname.find('.//tei:forename[@type="first"]', ns)
                surname_elem = persname.find('.//tei:surname', ns)
                
                forename = forename_elem.text if forename_elem is not None else ""
                surname = surname_elem.text if surname_elem is not None else ""
                
                if forename or surname:
                    full_name = f"{forename} {surname}".strip()
                    if full_name:
                        authors.append(full_name)
        
        return authors if authors else ["Authors not found"]
    
    def _extract_abstract(self, root, ns):
        """Extract abstract text"""
        abstract_elem = root.find('.//tei:abstract', ns)
        if abstract_elem is not None:
            # Get all text content from abstract
            abstract_text = self._get_element_text(abstract_elem)
            return self._clean_text(abstract_text)
        
        return "Abstract not found"
    
    def _extract_introduction(self, root, ns):
        """Extract introduction section"""
        # Look for introduction section
        sections = root.findall('.//tei:body//tei:div[@type="introduction"]', ns)
        
        if not sections:
            # Fallback: look for first section or section with "introduction" in title
            all_sections = root.findall('.//tei:body//tei:div', ns)
            for section in all_sections:
                head = section.find('.//tei:head', ns)
                if head is not None and head.text:
                    if 'introduction' in head.text.lower():
                        sections = [section]
                        break
            
            # If still no introduction found, take first section
            if not sections and all_sections:
                sections = [all_sections[0]]
        
        if sections:
            intro_text = self._get_element_text(sections[0])
            return self._clean_text(intro_text)
        
        return "Introduction not found"
    
    def _get_element_text(self, element):
        """Recursively get all text content from an XML element"""
        text_parts = []
        
        if element.text:
            text_parts.append(element.text)
        
        for child in element:
            text_parts.append(self._get_element_text(child))
            if child.tail:
                text_parts.append(child.tail)
        
        return " ".join(text_parts)
    
    def _clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = " ".join(text.split())
        return text.strip()

# def main():
#     """Example usage"""
#     # Initialize extractor
#     extractor = GrobidPDFExtractor()
    
#     # Path to your PDF file
#     pdf_path = "/mlcv2/WorkingSpace/Personal/quannh/Project/Project/ohmni/RAG/data/CV5.pdf"  # Replace with your PDF path
    
#     # Check if file exists
#     if not Path(pdf_path).exists():
#         print(f"PDF file not found: {pdf_path}")
#         return
    
#     print(f"Processing PDF: {pdf_path}")
#     print("This may take a few moments...")
    
#     # Extract information
#     result = extractor.process_pdf(pdf_path)
    
#     if result:
#         print("\n" + "="*50)
#         print("EXTRACTION RESULTS")
#         print("="*50)
        
#         print(f"\nTITLE:")
#         print(f"{result['title']}")
        
#         print(f"\nAUTHORS:")
#         for i, author in enumerate(result['authors'], 1):
#             print(f"{i}. {author}")
        
#         print(f"\nABSTRACT:")
#         print(f"{result['abstract'][:500]}..." if len(result['abstract']) > 500 else result['abstract'])
        
#         print(f"\nINTRODUCTION:")
#         print(f"{result['introduction'][:500]}..." if len(result['introduction']) > 500 else result['introduction'])
        
#         # Optionally save to JSON
#         output_file = "extracted_paper_info.json"
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(result, f, indent=2, ensure_ascii=False)
#         print(f"\nResults saved to: {output_file}")
        
#     else:
#         print("Failed to extract information from PDF")

# if __name__ == "__main__":
    # main()