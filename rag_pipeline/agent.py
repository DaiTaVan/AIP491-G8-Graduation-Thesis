from typing import Dict, List
from abc import abstractmethod
from llm import BaseLLM
from vector_database import LawBGEM3QdrantDatabase, Node
from embedding import BGEEmbedding
from retriever import LawRetriever
from reranker import RankGPTRerank
from knowledge_graph.neo4j_database import Neo4jDatabase


class BaseAgent:
    @abstractmethod
    def run(self, **kwargs):
        """
        Run the agent
        """

class Agent1(BaseAgent):
    """
    Chuyên gia phân loại vấn đề
    """
    def __init__(
            self,
            llm: BaseLLM,
            config: Dict
    ):
        self.llm = llm
        self.config = config
        self.prompt = self.config['prompt']
    
    def run(self, query):
        completion_query = self.prompt.format(input = query)
        completion_result = self.llm.generate(
            query = completion_query
        )
        return completion_result

class Agent2(BaseAgent):
    """
    Nhà phân tích các vấn đề về luật
    """
    def __init__(
            self,
            llm: BaseLLM,
            config: Dict
    ):
        self.llm = llm
        self.config = config
        self.prompt = self.config['prompt']
    
    def run(self, query):
        completion_query = self.prompt.format(input = query)
        completion_result = self.llm.generate(
            query = completion_query
        )
        list_new_questions = completion_result.split('\n')
        return list_new_questions

class Agent3(BaseAgent):
    """
    Tìm kiếm luật
    """
    def __init__(
            self,
            vector_database: LawBGEM3QdrantDatabase,
            embedding: BGEEmbedding,
            top_k: int = 10,
            alpha: float = 0.5
    ):
        self.vector_database = vector_database
        self.embedding = embedding
        self.top_k = top_k
        self.alpha = alpha

        self.retriever = LawRetriever(
            vector_database=self.vector_database,
            embedding=self.embedding,
            top_k=self.top_k,
            alpha=self.alpha
        )
    def run(self, query: str, query_filter: Dict = None):
        list_nodes = self.retriever.retrieve(
            query=query,
            filter=query_filter
        )
        return list_nodes

class Agent4(BaseAgent):
    """
    Rerank and get source node
    """
    def __init__(
            self,
            rerank: RankGPTRerank,
            graph_database: Neo4jDatabase,
    ): 
        self.rerank = rerank
        self.graph_database = graph_database
    
    def run(self, list_nodes: List[Node], query: str):

        new_list_nodes = self.rerank._postprocess_nodes(
            nodes=list_nodes,
            query=query
        )

        node_ids = []
        for node in new_list_nodes:
            node_id = node['metadata']['dieu_id']
            if node_id not in node_ids:
                node_ids.append(node_id)
        
        list_dieu_luat = [self.get_dieu_luat_theo_id(node_id) for node_id in node_ids]

        context = '\n\n'.join([f"{dieu_luat['title']}\n{dieu_luat['content']}" for dieu_luat in list_dieu_luat])

        return {
            'question': query,
            'context': context,
            'references': list_dieu_luat
        }

    
    def get_dieu_luat_theo_id(self, dieu_id: str):
        query = f"MATCH (n:DieuPhapDien {{id: \'{dieu_id}\'}}) RETURN n"

        with self.graph_database.driver.session() as session:
            result = session.run(query).data()[0]['n']
        return result


