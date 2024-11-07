from typing import Dict
from qdrant_client import models
from vector_database import LawBGEM3QdrantDatabase, Query
from embedding import BGEEmbedding

class LawRetriever:
    def __init__(
            self,
            vector_database: LawBGEM3QdrantDatabase,
            embedding: BGEEmbedding,
            top_k: int = 5,
            alpha: float = 0.5
    ):
        self.vector_database = vector_database
        self.embedding = embedding
        self.top_k = top_k 
        self.alpha = alpha
    
    def retrieve(self, query: str, filter: Dict):

        embedding_content = self.embedding.embed([query])[0]
        if filter is not None:
            query_filter = models.Filter(
                must=[
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(
                        value=value,
                    ),
                ) for key, value in filter.items()
                ]
            )

        query_object = Query(
            content=query,
            dense_vector=embedding_content['dense'],
            sparse_vector=embedding_content['sparse'],
            similarity_top_k=self.top_k,
            query_filter=query_filter
        )

        result = self.vector_database.query(query_object,self.alpha)

        return result

    
