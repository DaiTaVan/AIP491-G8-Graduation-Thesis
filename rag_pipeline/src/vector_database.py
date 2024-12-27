from qdrant_client import QdrantClient, models, AsyncQdrantClient
from typing import Dict, List, TypedDict

class Node(TypedDict):
    id: str
    dense_vector: List
    sparse_vector: Dict
    metadata: Dict

class NodeWithScore(Node):
    score: float

class Query(TypedDict):
    content: str
    dense_vector: List
    sparse_vector: Dict
    similarity_top_k: int
    query_filter: models.Filter = None

class LawBGEM3QdrantDatabase:

    database_name = "BoPhapDien"
    DENSE_VECTOR_NAME = "text-dense"
    SPARSE_VECTOR_NAME = "text-sparse"
    batch_size = 2
    max_retries = 3

    def __init__(
            self,
            url: str,
            api_key: str
    ):  
        self.url = url
        self.api_key = api_key
        self.client = QdrantClient(url=self.url, api_key= self.api_key)
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
    
    def query(self, query: Query, alpha: float):

        search_response = self.client.search_batch(
                collection_name=self.database_name,
                requests=[
                    models.SearchRequest(
                        vector=models.NamedVector(
                            name=self.DENSE_VECTOR_NAME,
                            vector=query["dense_vector"],
                        ),
                        limit=query["similarity_top_k"],
                        filter=query["query_filter"],
                        with_payload=True,
                    ),
                    models.SearchRequest(
                        vector=models.NamedSparseVector(
                            # Dynamically switch between the old and new sparse vector name
                            name=self.SPARSE_VECTOR_NAME,
                            vector=models.SparseVector(
                                indices=[int(ele) for ele in list(query["sparse_vector"].keys())],
                                values=list(query["sparse_vector"].values()),
                            ),
                        ),
                        limit=query["similarity_top_k"],
                        filter=query["query_filter"],
                        with_payload=True,
                    ),
                ],
            )

        # sanity check
        assert len(search_response) == 2
        dense_nodes = self.get_node_from_response(search_response[0])
        sparse_nodes = self.get_node_from_response(search_response[1])

        

        return self.relative_score_fusion(dense_nodes=dense_nodes,
                                          sparse_nodes=sparse_nodes,
                                          alpha = alpha,
                                          top_k=query["similarity_top_k"])


    def get_node_from_response(self, responses: List[models.ScoredPoint]):
        nodes = []

        for point in responses:
            payload = point.payload
            nodes.append(
                NodeWithScore(
                    id = point.id,
                    dense_vector=[],
                    sparse_vector={},
                    metadata=payload,
                    score=point.score
                )
            )

        return nodes
    

    def relative_score_fusion(
            self, 
            dense_nodes: List[NodeWithScore], 
            sparse_nodes: List[NodeWithScore], 
            alpha = 0.5,
            top_k = 10
    ):
        # deconstruct results
        sparse_result_similarities = [ele["score"] for ele in sparse_nodes]
        sparse_result_tuples = list(zip(sparse_result_similarities, sparse_nodes))
        sparse_result_tuples.sort(key=lambda x: x[0], reverse=True)

        dense_result_similarities = [ele["score"] for ele in dense_nodes]
        dense_result_tuples = list(zip(dense_result_similarities, dense_nodes))
        dense_result_tuples.sort(key=lambda x: x[0], reverse=True)

        # track nodes in both results
        all_nodes_dict = {x["id"]: x for x in dense_nodes}
        for node in sparse_nodes:
            if node["id"] not in all_nodes_dict:
                all_nodes_dict[node["id"]] = node

        # normalize sparse similarities from 0 to 1
        sparse_similarities = [x[0] for x in sparse_result_tuples]

        sparse_per_node = {}
        if len(sparse_similarities) > 0:
            max_sparse_sim = max(sparse_similarities)
            min_sparse_sim = min(sparse_similarities)

            # avoid division by zero
            if max_sparse_sim == min_sparse_sim:
                sparse_similarities = [max_sparse_sim] * len(sparse_similarities)
            else:
                sparse_similarities = [
                    (x - min_sparse_sim) / (max_sparse_sim - min_sparse_sim)
                    for x in sparse_similarities
                ]

            sparse_per_node = {
                sparse_result_tuples[i][1]["id"]: x
                for i, x in enumerate(sparse_similarities)
            }

        # normalize dense similarities from 0 to 1
        dense_similarities = [x[0] for x in dense_result_tuples]

        dense_per_node = {}
        if len(dense_similarities) > 0:
            max_dense_sim = max(dense_similarities)
            min_dense_sim = min(dense_similarities)

            # avoid division by zero
            if max_dense_sim == min_dense_sim:
                dense_similarities = [max_dense_sim] * len(dense_similarities)
            else:
                dense_similarities = [
                    (x - min_dense_sim) / (max_dense_sim - min_dense_sim)
                    for x in dense_similarities
                ]

            dense_per_node = {
                dense_result_tuples[i][1]["id"]: x
                for i, x in enumerate(dense_similarities)
            }
        

        # fuse the scores
        # fuse the scores
        fused_similarities = []
        for node_id in all_nodes_dict:
            sparse_sim = sparse_per_node.get(node_id, 0)
            dense_sim = dense_per_node.get(node_id, 0)
            fused_sim = (1 - alpha) * sparse_sim + alpha * dense_sim
            fused_similarities.append((fused_sim, all_nodes_dict[node_id]))

        fused_similarities.sort(key=lambda x: x[0], reverse=True)
        fused_similarities = fused_similarities[:top_k]

        final_nodes = []
        for ele in fused_similarities:
            fn_node = ele[1]
            fn_node["score"] = ele[0]
            final_nodes.append(fn_node)

        return final_nodes


        



