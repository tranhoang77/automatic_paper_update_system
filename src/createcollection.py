import os
from typing import List
from openai import OpenAI
from embedding import NomicEmbeddings

from pymilvus import (
    MilvusClient,
    DataType,
    Function,
    FunctionType,
)

class Database:
    def __init__(self, uri="http://192.168.20.156:19530"):
        self.uri = uri       
        self.client = MilvusClient(uri=self.uri)
        
    def create_collection(self, collection_name):
        analyzer_params = {
            "tokenizer": "standard",
            "filter": ["lowercase"],
        }

        schema = MilvusClient.create_schema()
        schema.add_field(
            field_name="id",
            datatype=DataType.INT64,
            is_primary=True,
            auto_id=True,
        )
        schema.add_field(
            field_name="content",
            datatype=DataType.VARCHAR,
            max_length=4000,
            analyzer_params=analyzer_params,
            enable_match=True,     
            enable_analyzer=True, 
        )
        schema.add_field(
            field_name="sparse_vector",
            datatype=DataType.SPARSE_FLOAT_VECTOR,
        )
        schema.add_field(
            field_name="dense_vector",
            datatype=DataType.FLOAT_VECTOR,
            dim=768,
        )
        schema.add_field(
            field_name="paper_authors",
            datatype=DataType.VARCHAR,
            max_length=500,
            analyzer_params=analyzer_params,
        )
        schema.add_field(
            field_name="title_paper",
            datatype=DataType.VARCHAR,
            max_length=500,
            analyzer_params=analyzer_params,
            enable_match=True,
            enable_analyzer=True,
        )
        schema.add_field(
            field_name="novelty",
            datatype=DataType.VARCHAR,
            max_length=4000,
            analyzer_params=analyzer_params,
            enable_math=True,
            enable_analyzer=True,
        )
        schema.add_field(
            field_name="pdf_url",
            datatype=DataType.VARCHAR,
            max_length=200,
            analyzer_params=analyzer_params,
            enable_math=True,
            enable_analyzer=True,
        )

        bm25_function = Function(
            name="bm25",
            function_type=FunctionType.BM25,
            input_field_names=["title_paper"],
            output_field_names="sparse_vector",
        )
        schema.add_function(bm25_function)

        index_params = MilvusClient.prepare_index_params()
        index_params.add_index(
            field_name="sparse_vector",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="BM25",
        )
        index_params.add_index(
            field_name="dense_vector",
            index_type="FLAT",
            metric_type="COSINE",
        )

        # Drop collection if it exists
        if self.client.has_collection(collection_name):
            self.client.drop_collection(collection_name)
            import time; 
            time.sleep(2)

        # Tạo collection mới
        self.client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
        )
        print(f"Collection '{collection_name}' created successfully")
        
    def insert_entity(self, entities, collection_name):
        """_summary_
        entity structure like this:
        {
            "content": str,
            "dense_vector": []*768,
            "paper_authors": str,
            "title_paper": str,
            "novelty" : str,
            "pdf_url" : str
        }
        """
        self.client.insert(collection_name, entities)
        self.client.flush(collection_name)
        print(f"Inserted {len(entities)} documents into '{collection_name}'")
            
        

