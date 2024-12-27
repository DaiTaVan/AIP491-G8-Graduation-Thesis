import argparse
import json
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Any, TypedDict, Literal
from datetime import datetime
# Required imports from the original system
from llm import Ollama, OpenAI
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM
from langchain_community.llms import HuggingFaceEndpoint

from langgraph.graph import StateGraph, START, END
from vector_database import LawBGEM3QdrantDatabase
from embedding import BGEEmbedding
from reranker import JinaRerank, RankGPTRerank
from knowledge_graph.neo4j_database import Neo4jDatabase

from agent import Agent1, Agent2, Agent3, Agent4, Agent5, Agent6

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'time': self.formatTime(record, self.datefmt),
            'name': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
        }
        return json.dumps(log_record)


# Configure logging with JsonFormatter and RotatingFileHandler at the top-level
handler = RotatingFileHandler("pipeline.log", maxBytes=5*1024*1024, backupCount=5)
handler.setFormatter(JsonFormatter())
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[handler, logging.StreamHandler()]
)


class AgentState(TypedDict, total=False):
    query: str
    agent1_output: Dict[str, Any]
    agent2_output: Dict[str, Any]
    agent3_output: Dict[str, Any]
    agent4_output: Dict[str, Any]
    agent5_output: Dict[str, Any]
    agent6_output: Dict[str, Any]
    retrieved_nodes: List[Any]
    final_answer_state: str
    final_context_nodes_str: str
    intermediate_steps: List[Any]
    enable_recursive: bool # Flag enable recursion
    recursive_check: bool  # Flag for recursion


class Pipeline:
    def __init__(
        self,
        openai_api_key: str,
        qdrant_url: str = "http://localhost:6333",
        qdrant_api_key: str = None,
        neo4j_uri: str = "neo4j://localhost",
        neo4j_auth: tuple = ("neo4j", "Abc12345"),
        config_path: str = None,
        legal_topics_path: str = "test.txt",
    ):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Pipeline...")

        # Set environment variable for OpenAI API key
        self.openai_api_key = openai_api_key
        os.environ["OPENAI_API_KEY"] = openai_api_key

        # Initialize models
        self.gpt_model = ChatOpenAI(temperature=0.1, model_name="gpt-4o")
        self.gpt_model_2 = ChatOpenAI(temperature=0.1, model_name="gpt-4o-mini")
        # self.ollama_model = OllamaLLM(model="qwen:2.5", temperature=0.7)

        # Database configurations
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.neo4j_uri = neo4j_uri
        self.neo4j_auth = neo4j_auth

        # Load configuration file
        self.config = {}
        if config_path:
            self.logger.info(f"Loading configuration from {config_path}")
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    self.config = json.load(file)
                self.logger.info("Configuration loaded successfully.")
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {e}")
                raise e
        else:
            self.logger.warning("No config path provided. Using default configuration.")

        # Load legal topics
        self.legal_topics = ""
        if legal_topics_path:
            try:
                with open(legal_topics_path, "r", encoding="utf-8") as file:
                    self.legal_topics = file.read()
                self.logger.info(f"Legal topics loaded from {legal_topics_path}.")
            except Exception as e:
                self.logger.error(f"Failed to load legal topics from {legal_topics_path}: {e}")
                # Decide whether to raise an error or continue without legal topics
                # For now, we'll continue with empty legal_topics
                self.logger.warning("Proceeding with empty legal topics.")
        else:
            self.logger.warning("No legal topics path provided. Using empty legal topics.")

        # Initialize vector database and retriever components
        self.vector_database = LawBGEM3QdrantDatabase(url=self.qdrant_url, api_key=self.qdrant_api_key)
        self.embedding_model = BGEEmbedding(model_name="bge-m3-finetune")

        DEFAULT_TOP_N = 3
        self.jina_reranker = JinaRerank(
            top_n=DEFAULT_TOP_N,
            model="jina-colbert-v2",
            api_key=""
        )

        self.gpt_reranker = RankGPTRerank(
            top_n=DEFAULT_TOP_N,
            llm=OpenAI(
                temperature=0,
                model_name="gpt-4o-mini"
            ),
        )

        self.graph_db = Neo4jDatabase(
            uri=self.neo4j_uri,
            username=self.neo4j_auth[0],
            password=self.neo4j_auth[1],
        )

        # Initialize agents
        self.agent1 = Agent1(config=self.config, model=self.gpt_model)
        self.agent2 = Agent2(config=self.config, model=self.gpt_model)
        self.agent3 = Agent3(
            # llm=self.gpt_model, 
            vector_database=self.vector_database, 
            embedding=self.embedding_model, 
            reranker=self.jina_reranker,
            top_k=10,
            alpha=0.5
        )
        self.agent4 = Agent4(
            # llm=self.gpt_model,
            # config=self.config,
            # rerank=self.gpt_reranker,
            graph_database=self.graph_db,
        )
        self.agent5 = Agent5(model=self.gpt_model, config=self.config)
        self.agent6 = Agent6(model=self.gpt_model, config=self.config)

        # Create the LangGraph workflow
        self.graph = self._create_graph()
        self.logger.info("Pipeline initialization complete.")

    def agent1_node(self, state: AgentState) -> AgentState:
        self.logger.info("Starting Agent1.")
        try:
            state["agent1_output"] = self.agent1.run(query=state["query"])
            self.logger.info(f"Agent1 Output: {state['agent1_output']}")
            state["intermediate_steps"].append("Agent1 completed.")
        except Exception as e:
            self.logger.error(f"Agent1 encountered an error: {e}")
            raise e
        return state

    def agent2_node(self, state: AgentState) -> AgentState:
        self.logger.info("Starting Agent2.")
        # question_category = state["agent1_output"].get("danh_muc_cau_hoi", "")
        
        # Use self.legal_topics loaded during initialization
        input_agent2 = f"Đề mục trong văn bản pháp luật Việt Nam: {self.legal_topics}" #\nLoại câu hỏi: {question_category}"
        self.logger.debug(f"Input to Agent2: {input_agent2}")

        try:
            state["agent2_output"] = self.agent2.run(input_agent2=input_agent2, query=state["query"])
            self.logger.info(f"Agent2 Output: {state['agent2_output']}")
            state["intermediate_steps"].append("Agent2 completed.")
        except Exception as e:
            self.logger.error(f"Agent2 encountered an error: {e}")
            raise e
        return state

    def agent3_node(self, state: AgentState) -> AgentState:
        self.logger.info("Starting Agent3 (Retrieval).")
        # Use initialized components
        difficulty = state["agent2_output"].get("do_kho", "Trung bình")
        params = {
            "Dễ": (3, 0.5, 2),
            "Trung bình": (5, 0.5, 3),
            "Khó": (5, 0.7, 5)
        }
        top_k, alpha, top_n = params.get(difficulty, (5, 0.5, 3))
        self.logger.debug(f"Retrieval Parameters - Difficulty: {difficulty}, Top K: {top_k}, Alpha: {alpha}, Top N: {top_n}")
        self.jina_reranker.update_top_n(n=top_n)
        self.agent3.update_top_k_and_alpha(top_k=top_k, alpha=alpha)
        self.agent3.reranker = self.jina_reranker
        # Prepare queries for retrieval
        list_query = [state["agent2_output"].get("cau_hoi_tang_cuong", "")] + state["agent2_output"].get("cau_hoi_phan_ra", [])
        self.logger.debug(f"List of Queries for Agent3: {list_query}")

        try:
            state["retrieved_nodes"] = self.agent3.run(list_query=list_query, original_query=state["query"])
            state["agent3_output"] = state["retrieved_nodes"]
            self.logger.info(f"Agent3 Retrieved Nodes: {state['retrieved_nodes']}")
            state["intermediate_steps"].append("Agent3 (Retrieval) completed.")
        except Exception as e:
            self.logger.error(f"Agent3 encountered an error: {e}")
            raise e
        return state

    def agent4_node(self, state: AgentState) -> AgentState:
        """Generates the final answer using retrieved information."""
        self.logger.info("Starting Agent4 (Final Answer).")

        try:
            state["final_answer_state"] = self.agent4.run(
                query=state["query"],
                retrieved_nodes=state["retrieved_nodes"],
                addition_info = state["agent2_output"]
            )
            state["agent4_output"] = state["final_answer_state"]
            self.logger.info(f"Agent4 Output: {state['final_answer_state']}")
            state["intermediate_steps"].append("Agent4 (Final Answer) completed.")
        except Exception as e:
            self.logger.error(f"Agent4 encountered an error: {e}")
            raise e
        return state

    def agent5_node(self, state: AgentState) -> AgentState:
        """Processes the final answer through Agent5."""
        self.logger.info("Starting Agent5.")
        try:
            final_content_context = state["final_answer_state"]
            list_contexts = [{"doc_no": ele[0], "Nội dung": ele[1]} for ele in final_content_context['contexts']]
            # Run Agent5
            state["agent5_output"] = self.agent5.run(state["query"], state['agent2_output'], str(list_contexts))
            self.logger.info(f"Agent5 Output: {state['agent5_output']}")
            if state["agent5_output"] is not None:
                state["recursive_check"] = state["agent5_output"].get('recursive', False)
                self.logger.debug(f"Recursive Check Flag: {state['recursive_check']}")
            state["intermediate_steps"].append("Agent5 completed.")
            return state
        except Exception as e:
            self.logger.error(f"Agent5 encountered an error: {e}")
            raise e

    def agent6_node(self, state: AgentState) -> AgentState:
        """Processes the output through Agent6 and generates the final Markdown output."""
        self.logger.info("Starting Agent6.")
        try:
            if state["agent2_output"] is None:
                self.logger.debug("agent2_output error, run agent6")
                state["agent6_output"] = self.agent6.run_single_shot(query_str = state["query"])
            elif len(state["agent2_output"]) == 0:
                if state["agent1_output"]["lien_quan_luat"].lower() == 'không':
                    state["agent6_output"] = "Xin lỗi, có thể câu hỏi của bạn không liên quan đến luật. Xin hãy hỏi lại hoặc cung cấp thêm thông tin. 😊"
                elif state["agent1_output"]["can_them_thong_tin"].lower() =='không':
                    state["agent6_output"] = self.agent6.run_single_shot(query_str = state["query"])    
            else:
                if state["agent5_output"] is None:
                    final_context_nodes = [ele[1] for ele in state["final_answer_state"]['contexts']][:3]
                else:
                    dict_context_node = {ele[0]: ele[1] for ele in state["final_answer_state"]['contexts']}
                    filter_node_ids = state["agent5_output"]["doc_numbers"][:5]
                    final_context_nodes = []
                    for node_id in filter_node_ids:
                        if node_id in dict_context_node.keys():
                            final_context_nodes.append(dict_context_node[node_id])
                    
                final_context_nodes_str = '\n'.join(final_context_nodes)
                state["final_context_nodes_str"] = final_context_nodes_str
                self.logger.debug(f"Updated final context nodes str: {state['final_context_nodes_str']}")

                state["agent6_output"] = self.agent6.run(state["query"], state["agent2_output"], final_context_nodes_str)
            
            self.logger.info(f"Agent6 Output: {state['agent6_output']}")
            state["intermediate_steps"].append("Agent6 completed.")
            # Update final_answer_state with Agent6's output
            state["final_answer_state"] = state["agent6_output"]
            self.logger.debug(f"Updated Final Answer State: {state['final_answer_state']}")
            return state
        except Exception as e:
            self.logger.error(f"Agent6 encountered an error: {e}")
            raise e

    def agent1_route(self, state: AgentState) -> Literal["agent2", "agent6"]:
            relate_legal = state["agent1_output"].get("lien_quan_luat", "Không")
            retrieval_analysis = state["agent1_output"].get("can_them_thong_tin", "Không")
            self.logger.debug(f"Routing Decision - Relate Legal: {relate_legal}, Retrieval Analysis: {retrieval_analysis}")

            if relate_legal == "Có" and retrieval_analysis == "Có":
                self.logger.info("Routing to Agent2 (Retrieval).")
                return "agent2"
            else:
                self.logger.info("Routing directly to Agent6.")
                return "agent6"
    
    def agent2_route(self, state: AgentState) -> Literal["agent3", "agent6"]:
        """Go to agent 6 directly"""
        agent2_output = state["agent2_output"]
        if agent2_output is None:
            self.logger.info("Routing to Agent6 because of error.")
            return "agent6"
        else:
            self.logger.info("Routing to Agent3 (Retrieval).")
            return "agent3"
    
    def recursion_route(self, state: AgentState) -> str:
        if state.get("recursive_check") and state["enable_recursive"]:
            self.logger.info("Recursion needed. Routing back to Agent2.")
            return "agent2"  # Re-running Agent2 as per recursion
        else:
            self.logger.info("No recursion. Routing to Agent6.")
            return "agent6"

    def _create_graph(self) -> StateGraph:
        self.logger.info("Creating LangGraph workflow.")
        workflow = StateGraph(AgentState)

        

        # Add nodes
        workflow.add_node("agent1", self.agent1_node)
        workflow.add_node("agent2", self.agent2_node)
        workflow.add_node("agent3", self.agent3_node)
        workflow.add_node("agent4", self.agent4_node)
        workflow.add_node("agent5", self.agent5_node)
        workflow.add_node("agent6", self.agent6_node)

        # Start with Agent1
        workflow.add_edge(START, "agent1")
        self.logger.debug("Added edge from START to Agent1.")

        # Conditional routing after Agent1
        workflow.add_conditional_edges(
            "agent1",
            self.agent1_route,
        )
        self.logger.debug("Added conditional edges after Agent1.")

        workflow.add_conditional_edges("agent2", self.agent2_route)
        self.logger.debug("Added conditional edges after Agent2.")

        workflow.add_edge("agent3", "agent4")
        workflow.add_edge("agent4", "agent5")

        # Conditional routing after Agent5 based on recursion
        

        workflow.add_conditional_edges(
            "agent5",
            self.recursion_route,
        )
        self.logger.debug("Added conditional edges after Agent5.")

        # End after Agent6
        workflow.add_edge("agent6", END)
        self.logger.debug("Added edge from Agent6 to END.")

        self.logger.info("LangGraph workflow creation complete.")
        return workflow.compile()

    def run(self, query: str) -> Dict[str, Any]:
        self.logger.info("Running the pipeline.")
        state: AgentState = {
            "query": query,
            "agent1_output": {},
            "agent2_output": {},
            "agent3_output": {},
            "agent4_output": {},
            "agent5_output": {},
            "agent6_output": {},
            "retrieved_nodes": [],
            "final_answer_state": "",
            "final_context_nodes_str": "",
            "intermediate_steps": [],
            "enable_recursive": False,
            "recursive_check": False
        }
        self.logger.debug(f"Initial State: {state}")

        try:
            result = self.graph.invoke(state)
            self.logger.info("Pipeline execution completed.")
            self.logger.debug(f"Final Result: {result}")
        except Exception as e:
            self.logger.error(f"Pipeline encountered an error: {e}")
            raise e

        return result

# Argument parser function
def parse_args():
    parser = argparse.ArgumentParser(description="Run the RAG Pipeline with arguments.")
    parser.add_argument(
        "--openai_api_key",
        type=str,
        default="",
        help="OpenAI API key."
    )
    parser.add_argument(
        "--qdrant_url",
        type=str,
        default="http://localhost:6333",
        help="Qdrant URL."
    )
    parser.add_argument(
        "--qdrant_api_key",
        type=str,
        default=None,
        help="Qdrant API key."
    )
    parser.add_argument(
        "--neo4j_uri",
        type=str,
        default="neo4j://localhost",
        help="Neo4j URI."
    )
    parser.add_argument(
        "--neo4j_user",
        type=str,
        default="neo4j",
        help="Neo4j username."
    )
    parser.add_argument(
        "--neo4j_password",
        type=str,
        default="Abc12345",
        help="Neo4j password."
    )
    parser.add_argument(
        "--config_path",
        type=str,
        default="/teamspace/studios/this_studio/AIP491-G8-Graduation-Thesis/rag_pipeline/config/agent.json",
        help="Path to the configuration file."
    )
    parser.add_argument(
        "--legal_topics_path",
        type=str,
        default="/teamspace/studios/this_studio/AIP491-G8-Graduation-Thesis/rag_pipeline/test.txt",
        help="Path to the legal topics file."
    )
    parser.add_argument(
        "--query",
        required=True,
        type=str,
        help="Query string to process."
    )
    return parser.parse_args()


if __name__ == "__main__":
    # Start logging for main execution
    logging.info("Starting the pipeline execution...")
    args = parse_args()
    logging.info(f"Arguments received: {args}")

    # Initialize the pipeline
    try:
        pipeline = Pipeline(
            openai_api_key=args.openai_api_key,
            qdrant_url=args.qdrant_url,
            qdrant_api_key=args.qdrant_api_key,
            neo4j_uri=args.neo4j_uri,
            neo4j_auth=(args.neo4j_user, args.neo4j_password),
            config_path=args.config_path,
            legal_topics_path=args.legal_topics_path,
        )
    except Exception as e:
        logging.error(f"Failed to initialize the pipeline: {e}")
        exit(1)

    # Run the pipeline
    try:
        result = pipeline.run(query=args.query)
    except Exception as e:
        logging.error(f"Failed to run the pipeline: {e}")
        exit(1)
    
    # Print the final answer
    print("Final Answer:", result.get("final_answer_state", "No answer generated."))
    print("Intermediate Steps:", result.get("intermediate_steps", []))
    # Tạo tên file dựa trên timestamp hiện tại
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"pipeline_result_{timestamp}.md"

    agents = [
        "agent1_output",
        "agent2_output",
        "agent3_output",
        "agent4_output",
        "agent5_output",
        "agent6_output"
    ]

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for agent_name in agents:
                f.write(f"----------{agent_name.upper()}-------------\n\n")
                agent_data = result.get(agent_name, {})
                # Chuyển dict sang JSON format cho dễ đọc, hoặc bạn có thể format theo ý thích
                agent_content = json.dumps(agent_data, indent=4, ensure_ascii=False)
                f.write(agent_content + "\n\n")
            f.write(result.get("final_answer_state", "No answer generated."))
        logging.info(f"Agent states have been saved to {output_file}")
    except Exception as e:
        logging.error(f"Failed to save agent states: {e}")
