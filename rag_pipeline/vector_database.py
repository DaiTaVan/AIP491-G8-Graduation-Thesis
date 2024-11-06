from qdrant_client import QdrantClient, models, AsyncQdrantClient
from typing import Dict, List, TypedDict

class Node(TypedDict):
    id: str
    dense_vector: List
    sparse_vector: Dict
    metadata: Dict

class Query:
    dense_vector: List
    sparse_vector: Dict
    similarity_top_k: int
    query_filter: models.Filter

class LawBGEM3QdrantDatabase:

    database_name = "BoPhapDien"
    DENSE_VECTOR_NAME = "text-dense"
    SPARSE_VECTOR_NAME = "text-sparse"
    batch_size = 2
    max_retries = 3

    def __init__(
            self,
            url: str
    ):  
        self.url = url
        self.client = QdrantClient(url=self.url)
        self.aclient = AsyncQdrantClient(url=self.url)
        if not self.check_database_exist():
            self.create_databse()
    
    def create_databse(self):
        self.client.create_collection(
            collection_name=self.database_name,
            vectors_config={
                self.DENSE_VECTOR_NAME: models.VectorParams(
                    size=1024, 
                    distance=models.Distance.COSINE, 
                    on_disk=True
                )
            },
            sparse_vectors_config={
                self.SPARSE_VECTOR_NAME: models.SparseVectorParams(
                    index=models.SparseIndexParams(
                        on_disk=True,
                    )
                ),
            },
        )

    def check_database_exist(self):
        return self.client.collection_exists(collection_name=self.database_name)
    
    def clear(self) -> None:
        """
        Clear the index.
        """
        self.client.delete_collection(collection_name=self.database_name)
        self.create_databse()
    
    def insert_nodes(self, nodes: List[Node]):
        node_ids = []
        payloads = []
        vectors = []

        for node in nodes:
            node_ids.append(node["id"])
            payloads.append(node["metadata"])
            vectors.append({
                # Dynamically switch between the old and new sparse vector name
                self.SPARSE_VECTOR_NAME: models.SparseVector(
                    indices=[int(ele) for ele in list(node["sparse_vector"].keys())],
                    values=list(node["sparse_vector"].values()),
                ),
                self.DENSE_VECTOR_NAME: node["dense_vector"],
            })
        
        points = [
                    models.PointStruct(id=node_id, payload=payload, vector=vector)
                    for node_id, payload, vector in zip(node_ids, payloads, vectors)
                ]

        self.client.upload_points(
            collection_name=self.database_name,
            points=points,
            batch_size=self.batch_size,
            max_retries=self.max_retries,
            wait=True,
        )
    
    def delete_nodes(self, node_ids: List[str]):
        self.client.delete(
            collection_name=self.database_name,
            points_selector=models.PointIdsList(
                points=node_ids,
            ),
        )
    
    def query(self, query: Query):

        search_response = self.client.search_batch(
                collection_name=self.database_name,
                requests=[
                    models.SearchRequest(
                        vector=models.NamedVector(
                            name=self.DENSE_VECTOR_NAME,
                            vector=query.dense_vector,
                        ),
                        limit=query.similarity_top_k,
                        filter=query.query_filter,
                        with_payload=True,
                    ),
                    models.SearchRequest(
                        vector=models.NamedSparseVector(
                            # Dynamically switch between the old and new sparse vector name
                            name=self.SPARSE_VECTOR_NAME,
                            vector=models.SparseVector(
                                indices=[int(ele) for ele in list(query.sparse_vector.keys())],
                                values=list(query.sparse_vector.values()),
                            ),
                        ),
                        limit=query.similarity_top_k,
                        filter=query.query_filter,
                        with_payload=True,
                    ),
                ],
            )

        # sanity check
        assert len(search_response) == 2
        pass


        



