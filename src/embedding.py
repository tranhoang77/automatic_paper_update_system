import torch
import torch.nn.functional as F
from typing import List
from transformers import AutoTokenizer, AutoModel
from langchain.embeddings.base import Embeddings

class NomicEmbeddings(Embeddings):
    """Custom embedding class cho Nomic AI model (chạy trên GPU nếu có)."""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            "nomic-ai/nomic-embed-text-v2-moe"
        )
        self.model = AutoModel.from_pretrained(
            "nomic-ai/nomic-embed-text-v2-moe", trust_remote_code=True
        )
        
        self.model.to(self.device)
        self.model.eval()

    def mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]  # token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed một danh sách documents (chạy trên GPU nếu có)."""
        prefixed_texts = [f"search_document: {t}" for t in texts]
        
        encoded_input = self.tokenizer(
            prefixed_texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        )
        encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
        
        with torch.no_grad():
            model_output = self.model(**encoded_input)
        
        embeddings = self.mean_pooling(model_output, encoded_input["attention_mask"])
        embeddings = F.normalize(embeddings, p=2, dim=1)
        
        return embeddings.cpu().numpy().tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed một câu query duy nhất (chạy trên GPU nếu có)."""
        query_text = f"search_query: {text}"
        
        encoded_input = self.tokenizer(
            [query_text],
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        )
        encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
        
        with torch.no_grad():
            model_output = self.model(**encoded_input)
        
        embedding = self.mean_pooling(model_output, encoded_input["attention_mask"])
        embedding = F.normalize(embedding, p=2, dim=1)
        
        return embedding.cpu().numpy().tolist()[0]
