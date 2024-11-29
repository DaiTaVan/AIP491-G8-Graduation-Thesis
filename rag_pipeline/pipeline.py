from typing import Tuple
import json
from llm import OpenAI, Qwen
from vector_database import LawBGEM3QdrantDatabase
from embedding import BGEEmbedding
from reranker import RankGPTRerank
from knowledge_graph.neo4j_database import Neo4jDatabase

from agent import Agent1, Agent2, Agent3, Agent4, Agent5


class Pipeline:
    def __init__(
            self,
            config_path: str,
            openai_api_key: str,
            qdrant_url: str,
            qdrant_api_key: str,
            bge_m3_model_name_or_path: str,
            neo4j_uri: str,
            neo4j_auth: Tuple,
            top_k_retriever: int = 5,
            alpha_retriever: float = 0.5,
            top_n_rerank: int = 3,
            verbose: bool = False
    ):
        self.config_path = config_path
        self.openai_api_key = openai_api_key
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.bge_m3_model_name_or_path = bge_m3_model_name_or_path
        self.neo4j_uri = neo4j_uri
        self.neo4j_auth = neo4j_auth
        self.top_k_retriever = top_k_retriever
        self.alpha_retriever = alpha_retriever
        self.top_n_rerank = top_n_rerank
        self.verbose = verbose

        self.llm_model_1 = OpenAI(
            api_key = self.openai_api_key,
            temperature = 0.1, 
            model_name = "gpt-4o"
        )
        self.llm_model_2 = OpenAI(
            api_key = self.openai_api_key,
            temperature = 0.1, 
            model_name = "gpt-4o-mini"
        )

        # self.llm_model_1 = Qwen(temperature=0.7, min_p=0.2, max_new_tokens=4096)
        # self.llm_model_2 = Qwen(url = 'http://localhost:8000/generate', temperature=0.7, top_p=0.8, max_new_tokens=2048)

        self.vector_database = LawBGEM3QdrantDatabase(
            url = self.qdrant_url,
            api_key=self.qdrant_api_key
        )
        self.embedding_model = BGEEmbedding(
                model_name = self.bge_m3_model_name_or_path
            )
        self.rerank = RankGPTRerank(
            top_n = self.top_n_rerank,
            llm = self.llm_model_1,
            verbose = self.verbose
        )


        self.graph_db = Neo4jDatabase(
                uri = self.neo4j_uri,
                username = self.neo4j_auth[0], 
                password = self.neo4j_auth[1]
            )

        with open(self.config_path) as f1:
            self.config = json.load(f1)
        
        self.agent1 = Agent1(
            llm = self.llm_model_1,
            config = self.config['Agent_1']
        )
        self.agent2 = Agent2(
            llm = self.llm_model_1,
            config = self.config['Agent_2']
        )
        self.agent3 = Agent3(
            config=self.config['Agent_3'],
            llm=self.llm_model_1,
            vector_database = self.vector_database,
            embedding = self.embedding_model,
            top_k = self.top_k_retriever,
            alpha = self.alpha_retriever,
            verbose = self.verbose
        )
        self.agent4 = Agent4(
            rerank = self.rerank,
            graph_database = self.graph_db
        )
        self.agent5 = Agent5(
            llm = self.llm_model_2,
            config = self.config['Agent_5']
        )
    
    def run(self, query: str):
        output_classify = None
        output_analysis = None
        condition_analysis = None
        list_retrieved_nodes = []
        condition_retriever = None
        list_contexts = []
        final_result = ""

        output_classify = self.agent1.run(query=query)
        if output_classify == 'Có':
            output_analysis, condition_analysis = self.agent2.run(query=query)
            if condition_analysis:
                list_retrieved_nodes, condition_retriever = self.agent3.run(list_query=output_analysis, original_query=query)
                if condition_retriever:
                    for new_query, retrieved_nodes in zip(output_analysis, list_retrieved_nodes):
                        reranked_context = self.agent4.run(list_nodes=retrieved_nodes, query = new_query)
                        list_contexts.append(reranked_context)
            else:
                list_retrieved_nodes, condition_retriever = self.agent3.run(list_query=[query], original_query=query)
                if condition_retriever:
                    reranked_context = self.agent4.run(list_nodes=list_retrieved_nodes[0], query = query)
                    list_contexts.append(reranked_context)
            
            final_result = self.agent5.run(query=query, list_contexts=list_contexts, condition_analysis = condition_analysis, condition_retriever = condition_retriever)
        else:
            print("No support")
            final_result = "Câu hỏi của bạn có vẻ không liên quan đến Luật. Hãy hỏi lại hoặc miêu tả rõ hơn."
        
        return {
            'final_result':final_result, 
            'condition_analysis': condition_analysis,
            'condition_retriever': condition_retriever,
            'list_contexts': list_contexts
        }
