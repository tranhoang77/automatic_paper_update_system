import os
import json
from pymilvus import Collection, connections
from embedding import NomicEmbeddings
from openai import OpenAI

class HybridSearcher:
    def __init__(self, collection_name: str, milvus_uri: str = 'http://192.168.20.156:19530', openai_api_key=None):
        # Kết nối Milvus
        connections.connect('default', uri=milvus_uri)
        self.collection = Collection(name=collection_name)
        self.embeddings = NomicEmbeddings()
        self.alpha = 0.5  # weight for dense
        self.beta = 0.5   # weight for sparse
        
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

    def search(self, query: str, top_k: int = 3):
        query_embedding = self.embeddings.embed_query(query)

        # --- search (BM25) ---
        sparse_search_params = {
            "metric_type": "BM25",
            "params": {}
        }
        sparse_hits = self.collection.search(
            data=[query],
            anns_field="sparse_vector",
            param=sparse_search_params,
            limit=top_k,
            output_fields=["content", "paper_authors", "title_paper", "novelty", "pdf_url"],
        )[0]

        # --- search dense (embedding) ---
        dense_search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        dense_hits = self.collection.search(
            data=[query_embedding],
            anns_field="dense_vector",
            param=dense_search_params,
            limit=top_k,
            output_fields=["content", "paper_authors", "title_paper", "novelty", "pdf_url"],
        )[0]

        results = {}

        for hit in sparse_hits:
            pk = hit.id
            results[pk] = {
                "hit": hit,
                "sparse_score": hit.score,
                "dense_score": 0.0
            }

        for hit in dense_hits:
            pk = hit.id
            if pk in results:
                results[pk]["dense_score"] = hit.score
            else:
                results[pk] = {
                    "hit": hit,
                    "sparse_score": 0.0,
                    "dense_score": hit.score
                }
                    
        results = {pk: info for pk, info in results.items() if info["dense_score"] >= 0.1}
        for info in results.values():
            info["hybrid_score"] = self.alpha * info["dense_score"] + self.beta * info["sparse_score"]

        sorted_list = sorted(
            results.values(),
            key=lambda x: x["hybrid_score"],
            reverse=True
        )

        final_list = []
        for paper in sorted_list:
            if paper['hybrid_score'] >= 1:
                final_list.append(paper)
            else:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4.1-nano",
                    messages = [
                        {
                            "role": "system",
                            "content": "You are an expert in academic research classification. Your job is to determine whether a research paper is relevant to a given topic, using only its title and abstract. Respond strictly with 'yes' or 'no'."
                        },
                        {
                            "role": "user",
                            "content": f"""Given the following information:

Topic: "{query}"

Title: "{paper["hit"].entity.get("title_paper")}"

Abstract: {paper["hit"].entity.get("content")}

Does this paper belong to the given topic? 
Respond with only one word: "yes" or "no"."""
                        }
                        ],
                    max_tokens=300,
                    temperature=0.7
                )
            
                choice = response.choices[0].message.content
                if 'yes' in choice:
                    final_list.append(paper)

        

        json_results = []
        for rank, info in enumerate(final_list, start=1):
            hit = info["hit"]
            json_results.append({
                "rank": rank,
                "primary_key": hit.id,
                "hybrid_score": round(info["hybrid_score"], 4),
                "sparse_score": round(info["sparse_score"], 4),
                "dense_score": round(info["dense_score"], 4),
                "content": hit.entity.get("content"),
                "paper_authors": hit.entity.get("paper_authors"),
                "title_paper": hit.entity.get("title_paper"),
                "novelty" : hit.entity.get("novelty"),
                "pdf_url": hit.entity.get("pdf_url")
            })

        os.makedirs("search_outputs", exist_ok=True)
        output_path = f"../search_outputs/results_{query}.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2)

        print(f"[✔] Kết quả đã được lưu vào: {output_path}")

        return final_list

