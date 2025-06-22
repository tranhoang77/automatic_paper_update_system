import requests
import re
import io
import PyPDF2
from datetime import datetime

class PaperProcessor:   
    def download_paper(self, url):
        """Download paper from URL."""
        try:
            if "arxiv.org" in url:
                if "/abs/" in url:
                    url = url.replace("/abs/", "/pdf/") + ".pdf"
                elif "/pdf/" not in url:
                    url += ".pdf"
            
            print(f"Downloading: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.content
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_content):
        """Extract text from PDF content."""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n+', '\n', text)
            
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None
    
    def extract_paper_info(self, text):
        """Extract basic paper information from text."""
        lines = text.split('\n')[:20]
        
        title = "Unknown Title"
        authors = "Unknown Authors"
        
        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                if not any(word in line.lower() for word in ['abstract', 'introduction', 'arxiv', 'page']):
                    title = line
                    break
        
        for i, line in enumerate(lines[1:6]):
            if any(indicator in line.lower() for indicator in ['university', 'institute', '@', 'department']):
                authors = lines[i] if lines[i].strip() else "Unknown Authors"
                break
        
        return title, authors
    
    def process(self, paper_input):
        """Process a single paper and store in vector database."""
        print(f"\n{'='*50}")
        print(f"Processing: {paper_input}")
        print(f"{'='*50}")
        
        # Download or read paper
        if paper_input.startswith(('http://', 'https://')):
            pdf_content = self.download_paper(paper_input)
            if not pdf_content:
                return None
        else:
            try:
                with open(paper_input, 'rb') as f:
                    pdf_content = f.read()
            except Exception as e:
                print(f"Error reading file {paper_input}: {e}")
                return None
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_content)
        if not text:
            return None
        
        # Extract paper info
        title, authors = self.extract_paper_info(text)
        print(f"Title: {title}")
        print(f"Authors: {authors}")
        return text, title, authors
        
        