from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from abc import abstractmethod
import json
from llm import BaseLLM
from vector_database import LawBGEM3QdrantDatabase, NodeWithScore
from embedding import BGEEmbedding
from retriever import LawRetriever
from reranker import RankGPTRerank, JinaRerank
from knowledge_graph.neo4j_database import Neo4jDatabase
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field, ValidationError
from abc import ABC, abstractmethod
from langchain.chains import LLMChain
import os

class BaseAgent:
    @abstractmethod
    def run(self, **kwargs):
        """
        Run the agent
        """

class LawQuestionAnalysis(BaseModel):
    lien_quan_luat: str = Field(
        description="Xác định xem câu hỏi có cần phân tích hay không: 'Có' hoặc 'Không'"
    )
    danh_muc_cau_hoi: str = Field(
        description="Danh mục cụ thể trong từng loại câu hỏi"
    )

class LawQuestionAnalysisV2(BaseModel):
    lien_quan_luat: str = Field(
        description="Xác định xem câu hỏi có liên quan đến luật hay không: 'Có' hoặc 'Không'"
    )
    can_them_thong_tin: str = Field(
        description="Xác định xem câu hỏi có cần thêm thông tin về các điều luật không: 'Có' hoặc 'Không'"
    )

class Agent1(BaseAgent):
    def __init__(self, config, model):
        """
        Initialize the Agent1 with the given configuration and model.

        :param config: A dictionary containing configuration parameters.
        :param model: The language model to be used (e.g., ollama_model).
        """
        # Define the JSON output parser using the Pydantic model
        # self.parser = JsonOutputParser(pydantic_object=LawQuestionAnalysis)
        self.parser = JsonOutputParser(pydantic_object=LawQuestionAnalysisV2)
        
        # Create the prompt template using the configuration
        self.prompt = PromptTemplate(
            # template=config['Agent_1']['prompt'],
            template=config['Agent_1']['prompt_2'],
            input_variables=["query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        
        # Set up the pipeline: prompt -> model -> parser
        self.chain = self.prompt | model | self.parser

    def run(self, query: str) -> LawQuestionAnalysisV2:
        """
        Run the agent with the given query.

        :param query: The legal question to analyze.
        :return: An instance of LawQuestionAnalysis containing the analysis.
        :raises ValueError: If the model's response is invalid or cannot be parsed.
        """
        try:
            # Invoke the chain with the provided query
            response = self.chain.invoke({"query": query})
            return response  # This should be a LawQuestionAnalysis instance
        except ValidationError as ve:
            # Handle Pydantic validation errors
            print(f"Validation error: {ve}")
            raise ValueError("Received invalid JSON response from the model.") from ve
        except Exception as e:
            # Handle other potential exceptions
            print(f"An error occurred: {e}")
            raise ValueError("An unexpected error occurred while processing the query.") from e

class EnhancedLawAnalysis(BaseModel):
    chu_de_lien_quan: list = Field(description="Danh sách đề mục pháp luật có liên quan.")
    chu_the_phap_ly: list = Field(description="Danh sách chủ thể liên quan trong câu hỏi pháp luật.")
    doi_tuong_phap_ly: list = Field(description="Danh sách khách thể hoặc hành vi liên quan trong câu hỏi pháp luật.")
    noi_dung_phap_ly: list = Field(description="Danh sách nội dung pháp luật, quyền, hoặc nghĩa vụ được xác định.")
    cau_hoi_tang_cuong: str = Field(description="Phiên bản câu hỏi được tăng cường hoặc làm rõ để tối ưu hóa việc truy xuất dữ liệu.")
    do_kho: str = Field(description="Mức độ khó của câu hỏi: 'Dễ', 'Trung bình', hoặc 'Khó'.")
    cau_hoi_phan_ra: list = Field(description="Danh sách câu hỏi phân rã nếu câu hỏi thuộc mức trung bình hoặc khó, ngược lại để trống.")

# Define the Agent2 class
class Agent2(BaseAgent):
    def __init__(self, config, model):
        """
        Initialize Agent2 with the given configuration and model.

        :param config: A dictionary containing configuration parameters.
        :param model: The language model to be used (e.g., ChatOpenAI).
        """

        self.max_retries = 0
        # Define the JSON output parser using the Pydantic model
        self.parser = JsonOutputParser(pydantic_object=EnhancedLawAnalysis)
        
        # Create the prompt template using the configuration
        self.prompt = PromptTemplate(
            template=config["Agent_2"]["prompt"],
            input_variables=["input_agent2", "query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        
        # Set up the pipeline: prompt -> model -> parser
        self.chain = self.prompt | model | self.parser

    def run(self, input_agent2: str, query: str) -> EnhancedLawAnalysis:
        """
        Run Agent2 with the given inputs.

        :param input_agent2: Input derived from Agent1's analysis.
        :param query: The original legal question.
        :return: An instance of EnhancedLawAnalysis containing the detailed analysis.
        :raises ValueError: If the model's response is invalid or cannot be parsed.
        """
        
        current_retry = 0
        while True:
            try:
                # Invoke the chain with the provided inputs
                response = self.chain.invoke({"input_agent2": input_agent2, "query": query})
                return response  # This should be an EnhancedLawAnalysis instance
            except ValidationError as ve:
                # Handle Pydantic validation errors
                print(f"Validation error: {ve}")
                if current_retry == self.max_retries:
                    # raise ValueError("Received invalid JSON response from the model.") from ve
                    return None
            except Exception as e:
                # Handle other potential exceptions
                print(f"An error occurred: {e}")
                if current_retry == self.max_retries:
                    # raise ValueError("An unexpected error occurred while processing the query.") from e
                    return None
            current_retry += 1

class Agent3(BaseAgent):
    """
    Tìm kiếm luật
    """
    def __init__(
            self,
            llm,
            vector_database: LawBGEM3QdrantDatabase,
            embedding: BGEEmbedding,
            reranker: JinaRerank,
            top_k: int = 10,
            alpha: float = 0.5,
            verbose: bool = False
    ):
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
        self.reranker = reranker
    
    def update_top_k_and_alpha(self, top_k: int, alpha: float):
        self.top_k = top_k
        self.alpha = alpha
        self.retriever = LawRetriever(
            vector_database=self.vector_database,
            embedding=self.embedding,
            top_k=self.top_k,
            alpha=self.alpha,
            verbose=self.verbose
        )

    def run(self, list_query: List[str], query_filter: Dict = None, original_query: str=""):
        list_result = self.retriever.retrieve(
            list_query=list_query,
            filter=query_filter,
        )
        list_reranked_nodes = []
        for i, q in enumerate(list_query):
            reranked_nodes_sub_q = self.reranker._postprocess_nodes(
                        nodes=list_result[i],
                        query=q
                    )
            list_reranked_nodes.extend(reranked_nodes_sub_q)
        return list_reranked_nodes

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
    
    def run(self, retrieved_nodes: List[NodeWithScore], query: str):
        # new_list_nodes = self.rerank._postprocess_nodes(
        #     nodes=retrieved_nodes,
        #     query=query
        # )
        new_list_nodes = retrieved_nodes

        node_ids = []
        node_titles = []
        for node in new_list_nodes:
            node_id = node['metadata']['dieu_id']
            if node_id not in node_ids:
                node_ids.append(node_id)
                node_titles.append(node['metadata']['content'].split('\n')[0])
        
        list_dieu_luat = [self.get_dieu_luat_theo_id(node_id) for node_id in node_ids]

        dict_dieu_luat_lien_quan =  {node_id: self.get_dieu_luat_lien_quan_theo_id(node_id) for node_id in node_ids}
        print(dict_dieu_luat_lien_quan)
#        Thêm llm check dieu liên quan và xóa bớt đi 
        contexts = [(node_id, self.get_context_by_dieu_luat(dieu_luat, node_title)) for node_id, dieu_luat, node_title in zip(node_ids, list_dieu_luat, node_titles)]
        # reranked_context['topic'][0].get('ChuDePhapdien')['title'] + ' - ' + reranked_context['topic'][0].get('DeMucPhapdien')['title']
        topic = [self.get_parent_of_dieu_luat_by_id(node_id).get('ChuDePhapdien')['title'] + ' - ' + \
            self.get_parent_of_dieu_luat_by_id(node_id).get('DeMucPhapdien')['title']\
            for node_id in node_ids]

        return {
            'question': query,
            'contexts': contexts,
            'references': list_dieu_luat,
            'topic': topic
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
    
    def get_dieu_luat_lien_quan_theo_id(self, dieu_id: str):
        query = f"MATCH (n:DieuPhapDien {{id: \'{dieu_id}\'}})-[r:RELATE_TO]->(m) RETURN m"
        with self.graph_database.driver.session() as session:
            result = session.run(query).data()
            result = [ele["m"] for ele in result]
        return result
    
    def get_parent_of_dieu_luat_by_id(self, dieu_id: str):
        
            def _get_parent_of_node(node_id: str, node_type: str):
                query = f"MATCH (n:{node_type} {{id:\'{node_id}\'}}) RETURN n"
                with self.graph_database.driver.session() as session:
                    result = session.run(query).data()[0]['n']

                return result
            
            parent_dict = {}

            dieu_node = self.get_dieu_luat_theo_id(dieu_id)
            parent_id = dieu_node['parent']
            parent_type = dieu_node['parent_type']
            node_type = dieu_node['label']
            
            while node_type != 'BoPhapDien':
                parent_node = _get_parent_of_node(parent_id, parent_type)
                if 'parent' not in parent_node.keys():
                    break
                parent_id = parent_node['parent']
                parent_type = parent_node['parent_type']
                node_type = parent_node['label']
                parent_dict[node_type] = parent_node

            return parent_dict


class RelatedLegalRules(BaseModel):
    recursive: bool = Field(
        description="Xác định xem có cần lặp lại bước hai không: 'Có' hoặc 'Không'"
    )
    doc_numbers: List[str]= Field(
        description="Lấy `doc_no` của ngữ cảnh cung cấp ở trên"
    )
    reference_ids: List[str] = Field(
        description="Lấy `reference_id` của ngữ cảnh cung cấp ở trên"
    )

class Agent5(BaseAgent):
    def __init__(self, config, model):
        """
        Supervise and compress data using LLM.

        :param config: A dictionary containing configuration parameters.
        :param model: The language model to be used (e.g., ollama_model).
        """
        # Define the JSON output parser using the Pydantic model
        self.parser = JsonOutputParser(pydantic_object=RelatedLegalRules)
        
        # Create the prompt template using the configuration
        self.prompt = PromptTemplate(
            template=config['Agent_5']['prompt'],
            input_variables=["query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        
        # Set up the pipeline: prompt -> model -> parser
        self.chain = self.prompt | model | self.parser

    def run(self, query: str, context: str) -> RelatedLegalRules:
        """
        Run the agent with the given query.

        :param query: The legal question to analyze.
        :return: An instance of RelatedLegalRules containing the analysis.
        :raises ValueError: If the model's response is invalid or cannot be parsed.
        """
        try:
            # Invoke the chain with the provided query
            response = self.chain.invoke({"query": query, "context_str": context})
            return response  # This should be a RelatedLegalRules instance
        except ValidationError as ve:
            # Handle Pydantic validation errors
            print(f"Validation error: {ve}")
            raise ValueError("Received invalid JSON response from the model.") from ve
        except Exception as e:
            # Handle other potential exceptions
            print(f"An error occurred: {e}")
            raise ValueError("An unexpected error occurred while processing the query.") from e
            print(f"Error occurred: {e}")
            return "An error occurred while processing the request."

class Agent6(BaseAgent):
    def __init__(self, config, model):
        """
        Initialize Agent6 with the given configuration and model.

        :param config: A dictionary containing configuration parameters.
        :param model: The language model to be used (e.g., OpenAI).
        """

        # Create the prompt template using the configuration
        self.prompt_check_instruct = PromptTemplate(
            template=config['Agent_6']['prompt_check_instruct'],
            input_variables=["query_str"],
        )
        self.prompt_no_instruct = PromptTemplate(
            template=config['Agent_6']['prompt'],
            input_variables=["query_str", "analysis_str", "context_str"],
        )
        self.prompt_instruct = PromptTemplate(
            template=config['Agent_6']['prompt_instruct'],
            input_variables=["query_str", "analysis_str", "context_str"],
        )
        self.model = model
        
        # Create the LLMChain
        self.chain_check_instruct = LLMChain(llm=self.model, prompt=self.prompt_check_instruct)
        self.chain_no_instruct = LLMChain(llm=self.model, prompt=self.prompt_no_instruct)
        self.chain_instruct = LLMChain(llm=self.model, prompt=self.prompt_instruct)
    

    def check_instruct(self, query_str: str):
        
        check_instruct = self.chain_check_instruct.run({"query_str": query_str}).strip().rstrip().lower()
        print('check_instruct', check_instruct)
        if check_instruct == 'không':
            return False
        else:
            return True


    def run(self, query_str: str, analysis_str: str, context_str: str):
        """
        Run Agent6 with the given inputs to generate the final report.

        :param query_str: The original legal question from the user.
        :param analysis_str: The detailed analysis from Agent1.
        :param context_str: The related legal context from Agent2.
        :return: An instance of FinalReport containing the summarized output.
        :raises ValueError: If the model's response is invalid or cannot be parsed.
        """
        try:
            # Prepare the inputs for the prompt
            inputs = {
                    "query_str": query_str,
                    "analysis_str": analysis_str,
                    "context_str": context_str,
                }
            if self.check_instruct(query_str=query_str):
                # Run the LLMChain
                result = self.chain_instruct.run(inputs)
            else:
                # Run the LLMChain
                result = self.chain_no_instruct.run(inputs)

            return result
        except ValidationError as ve:
            # Handle Pydantic validation errors
            print(f"Validation error in Agent6: {ve}")
            raise ValueError("Received invalid JSON response from Agent6.") from ve
        except Exception as e:
            # Handle other potential exceptions
            print(f"Error in Agent6: {e}")
            raise ValueError("An unexpected error occurred while processing the query in Agent6.") from e

    def run_single_shot(self, query_str: str):
        return self.model.invoke(query_str).content
