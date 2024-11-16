from typing import Dict, List
from abc import abstractmethod
import json
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
        self.condition_prompt = self.config['condition_prompt']
        self.prompt = self.config['prompt']
    
    def run(self, query):
        completion_condition_query = self.condition_prompt.format(input = query)
        completion_condition_result = self.llm.generate(
            query = completion_condition_query
        )
        list_new_questions = []
        # completion_condition_result = "Có"
        if completion_condition_result == "Có":
            completion_query = self.prompt.format(input = query)
            completion_result = self.llm.generate(
                query = completion_query
            )
            list_new_questions = completion_result.split('\n')

        return list_new_questions, completion_condition_result == "Có"
class Agent3(BaseAgent):
    """
    Tìm kiếm luật
    """
    def __init__(
            self,
            config: Dict,
            llm: BaseLLM,
            vector_database: LawBGEM3QdrantDatabase,
            embedding: BGEEmbedding,
            top_k: int = 10,
            alpha: float = 0.5,
            verbose: bool = False
    ):
        self.config = config
        self.condition_prompt = self.config['condition_prompt']
        self.llm = llm
        self.vector_database = vector_database
        self.embedding = embedding
        self.top_k = top_k
        self.alpha = alpha
        self.verbose = verbose

        self.retriever = LawRetriever(
            vector_database=self.vector_database,
            embedding=self.embedding,
            top_k=self.top_k,
            alpha=self.alpha,
            verbose=self.verbose
        )
    def run(self, list_query: List[str], query_filter: Dict = None, original_query: str=""):
        
        completion_condition_query = self.condition_prompt.format(input = original_query)
        completion_condition_result = self.llm.generate(
            query = completion_condition_query
        )

        list_result = []
        if completion_condition_result == "Có":
            list_result = self.retriever.retrieve(
                list_query=list_query,
                filter=query_filter,

            )
        return list_result, completion_condition_result == "Có"

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
        node_titles = []
        for node in new_list_nodes:
            node_id = node['metadata']['dieu_id']
            if node_id not in node_ids:
                node_ids.append(node_id)
                node_titles.append(node['metadata']['content'].split('\n')[0])
        
        list_dieu_luat = [self.get_dieu_luat_theo_id(node_id) for node_id in node_ids]



        contexts = [(node_id, self.get_context_by_dieu_luat(dieu_luat, node_title)) for node_id, dieu_luat, node_title in zip(node_ids, list_dieu_luat, node_titles)]

        return {
            'question': query,
            'contexts': contexts,
            'references': list_dieu_luat
        }

    def get_context_by_dieu_luat(self, dieu_luat: Dict, node_title: str):
        dieu_title = ' '.join(dieu_luat['title'].split(' ')[2:])
        dieu_content = dieu_luat['content']
        dieu_source = json.loads(dieu_luat['source'])
        tlplg_title = self.get_tai_lieu_phap_luat_goc_title_by_id(dieu_source["id"])
        dieu_number = dieu_source["location"].split('_')[-1]

        context = ""
        if dieu_number != "":
            context  = f"Điều {dieu_number} {tlplg_title}: {dieu_title}\n{dieu_content}"
        else:
            context = f"{node_title}\n{dieu_content}"

        return context
        
    def get_dieu_luat_theo_id(self, dieu_id: str):
        query = f"MATCH (n:DieuPhapDien {{id: \'{dieu_id}\'}}) RETURN n"

        with self.graph_database.driver.session() as session:
            result = session.run(query).data()[0]['n']
        return result
    
    def get_tai_lieu_phap_luat_goc_title_by_id(self, tlplg_id: str):
        query = f"MATCH (n:TaiLieuPhapLuatGoc {{id: \'{tlplg_id}\'}}) RETURN n"

        with self.graph_database.driver.session() as session:
            result = session.run(query).data()[0]['n']['title']
        return result
    

class Agent5(BaseAgent):
    """
    Sumarize and answer
    """
    def __init__(
            self,
            llm: BaseLLM,
            config: Dict
    ):
        self.llm = llm
        self.config = config
        self.prompt = self.config['prompt']
        self.prompt_have_revevant_laws_no_reasoning_questions = \
            self.config['prompt_have_revevant_laws_no_reasoning_questions']
        self.prompt_have_reasoning_questions_no_relevant_laws = \
            self.config['prompt_have_reasoning_questions_no_relevant_laws']
        self.prompt_no_reasoning_questions_no_relevant_laws = \
            self.config['prompt_no_reasoning_questions_no_relevant_laws']


    def run(self, query: str, list_contexts: List, condition_analysis: bool, condition_retriever: bool):
        
        reasoning_questions = ''
        relevant_laws = ''

        if condition_analysis:
            reasoning_questions = "\n".join([ele['question'] for ele in list_contexts])
        if condition_retriever:
            list_ids = []
            list_text_of_contexts = []
            for element in list_contexts:
                for sub_element in element['contexts']:
                    if sub_element[0] not in list_ids:
                        list_ids.append(sub_element[0])
                        list_text_of_contexts.append(sub_element[1])

            relevant_laws = "\n".join(list_text_of_contexts)

        completion_query = ''
        if condition_analysis and condition_retriever:

            completion_query = self.prompt.format(
                root_question = query, 
                reasoning_questions = reasoning_questions, 
                relevant_laws = relevant_laws
            )
        elif condition_analysis and not condition_retriever:
            completion_query = self.prompt_have_reasoning_questions_no_relevant_laws.format(
                root_question = query, 
                reasoning_questions = reasoning_questions, 
            )
        elif not condition_analysis and condition_retriever:
            completion_query = self.prompt_have_revevant_laws_no_reasoning_questions.format(
                root_question = query, 
                relevant_laws = relevant_laws
            )
        else:
            completion_query = self.prompt_no_reasoning_questions_no_relevant_laws.format(
                root_question = query,
            )
        completion_result = self.llm.generate(
            query = completion_query
        )


        return completion_result