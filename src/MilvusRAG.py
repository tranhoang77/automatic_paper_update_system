from embedding import NomicEmbeddings
from createcollection import Database
from extractpaper import GrobidPDFExtractor
from openai import OpenAI
import numpy as np
import os

class System:
    def __init__(self, collection_name, openai_api_key=None):
        print("connecting to database")
        self.collection_name = collection_name
        self.database = Database()
        self.database.create_collection(collection_name=collection_name)
        
        print("loading embedding model...")
        self.embedding_model = NomicEmbeddings()
        
        print("connecting to Grobid ...")
        self.extract_paper = GrobidPDFExtractor()
        
        print("conecting to openai...")
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
        else:
            # Will use OPENAI_API_KEY environment variable
            self.openai_client = OpenAI()

        try:
            self.openai_client.models.list()
            print("✓ OpenAI client initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize OpenAI client: {e}")
            print("Please check your API key and internet connection")
            raise
    
    def generate_summary(self, text, title):
        """Generate summary using OpenAI GPT-4."""
        try:
            if len(text) > 15000:
                text = text[:15000] + "..."
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano", 
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert academic summarizer. Your task is to produce a concise summary "
                            "of a research paper using only its title and abstract. Focus strictly on the core problem, "
                            "approach, and main contributions. Do not speculate or add extra information. "
                            "Keep the summary short and factual."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"""Title: "{title}"

                Abstract:
                {text}

                SUMMARY:"""
                        }
                    ],
                    max_tokens=300,
                    temperature=0.3
                )
                
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Error generating summary."
            
    def analyze_novelty(self, text, title):
        """Analyze the novelty of the paper using OpenAI GPT-4."""
        try:
            # Truncate text if too long
            if len(text) > 15000:
                text = text[:15000] + "..."
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a critical academic reviewer. Your task is to identify what is truly novel "
                            "in a research paper, based solely on its title and introduction. "
                            "Only highlight new methods, ideas, perspectives, or contributions. Ignore general motivation or background."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"""Given the following information:

            Title: "{title}"

            Introduction:
            {text}

            What is the novelty of this paper?

            Respond with a concise NOVELTY ANALYSIS — no more than 4 sentences. Focus only on what's new compared to existing research."""
                    }
                ],
                max_tokens=250,
                temperature=0.3,
            )

            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error analyzing novelty: {e}")
            return "Error analyzing novelty."
        
    def process_paper(self, path_paper_list, downloader=None):
        entities = []
        for i, pdf_path in enumerate(path_paper_list, 1):
            print(f"\n[{i}/{len(path_paper_list)}] Processing paper...")
            
            # read author, introduction, title, abstract
            result = self.extract_paper.process_pdf(pdf_path)
            title = result['title']
            authors =  result['authors']
            abstract = result['abstract']
            introduction = result['introduction']
            hash_id = os.path.basename(pdf_path).split('.')[0]
            pdf_url = downloader.get_abstract_url_from_hash(hash_id) if downloader else None
            
            authors = ", ".join(authors)
            
            # summary
            summary = self.generate_summary(abstract, title)
            # novelty
            novety = self.analyze_novelty(introduction, title)
            
            #vector 768 dim
            embedding_list = self.embedding_model.embed_documents([summary])
            embedding_vector = embedding_list[0]
            embedding_np = np.array(embedding_vector, dtype=np.float32)

                        
            entities.append({
                "content": summary,
                "dense_vector": embedding_np,
                "paper_authors": authors,
                "title_paper": title,
                "novelty" : novety,
                "pdf_url" : pdf_url,
            })
        
        # insert to database
        print("inserting to database")
        self.database.insert_entity(entities=entities, collection_name=self.collection_name)
        
        
            
            
            
            
            
            
            
            
            
            
            
            
