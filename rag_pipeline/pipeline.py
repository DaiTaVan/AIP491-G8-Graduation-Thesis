import argparse
import json
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Any, TypedDict

# Required imports from the original system
from llm import Ollama, OpenAI
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM

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
    intermediate_steps: List[Any]
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
        self.gpt_model = ChatOpenAI(temperature=0.4, model_name="gpt-4o-mini")
        self.ollama_model = OllamaLLM(model="qwen:2.5", temperature=0.7)

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
        self.embedding_model = BGEEmbedding(model_name="BAAI/bge-m3")

        DEFAULT_TOP_N = 3
        self.jina_reranker = JinaRerank(
            top_n=DEFAULT_TOP_N,
            model="jina-colbert-v2",
            api_key="jina_ac22e30cbc5b42eaa84b191d452e2d7aaTEwrOsPnT4LUI5F-guMJPr01A1C"
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
            llm=self.gpt_model,
            vector_database=self.vector_database,
            embedding=self.embedding_model,
            reranker=self.jina_reranker,
            top_k=10,
            alpha=0.5
        )
        self.agent4 = Agent4(
            rerank=self.gpt_reranker,
            graph_database=self.graph_db
        )
        self.agent5 = Agent5(model=self.gpt_model, config=self.config)
        self.agent6 = Agent6(model=self.gpt_model, config=self.config)

        # Create the LangGraph workflow
        self.graph = self._create_graph()
        self.logger.info("Pipeline initialization complete.")

    def agent1_node(self, state: AgentState) -> AgentState:
        self.logger.info("Starting Agent1.")
        agent1 = self.agent1
        try:
            state["agent1_output"] = agent1.run(query=state["query"])
            self.logger.info(f"Agent1 Output: {state['agent1_output']}")
            state["intermediate_steps"].append("Agent1 completed.")
        except Exception as e:
            self.logger.error(f"Agent1 encountered an error: {e}")
            raise e
        return state

    def agent2_node(self, state: AgentState) -> AgentState:
        self.logger.info("Starting Agent2.")
        question_category = state["agent1_output"].get("danh_muc_cau_hoi", "")
        
        # Use self.legal_topics loaded during initialization
        input_agent2 = f"Đề mục trong văn bản pháp luật Việt Nam: {self.legal_topics}\nLoại câu hỏi: {question_category}"
        self.logger.debug(f"Input to Agent2: {input_agent2}")

        agent2 = self.agent2
        try:
            state["agent2_output"] = agent2.run(input_agent2=input_agent2, query=state["query"])
            self.logger.info(f"Agent2 Output: {state['agent2_output']}")
            state["intermediate_steps"].append("Agent2 completed.")
        except Exception as e:
            self.logger.error(f"Agent2 encountered an error: {e}")
            raise e
        return state

    def retrieval_node(self, state: AgentState) -> AgentState:
        self.logger.info("Starting Agent3 (Retrieval).")
        difficulty = state["agent2_output"].get("do_kho", "Trung bình")
        params = {
            "Dễ": (3, 0.5, 2),
            "Trung bình": (5, 0.5, 3),
            "Khó": (8, 0.7, 5)
        }
        top_k, alpha, top_n = params.get(difficulty, (5, 0.5, 3))
        self.logger.debug(f"Retrieval Parameters - Difficulty: {difficulty}, Top K: {top_k}, Alpha: {alpha}, Top N: {top_n}")
        self.jina_reranker.update_top_n(n=top_n)
        self.agent3.update_top_k_and_alpha(top_k=top_k, alpha=alpha)
        self.agent3.reranker = self.jina_reranker
        # Prepare queries for retrieval
        list_query = [state["agent2_output"].get("cau_hoi_tang_cuong", "")] + state["agent2_output"].get("cau_hoi_phan_ra", [])
        state["retrieved_nodes"] = self.agent3.run(list_query=list_query, original_query=state["query"])
        # Use initialized components
        agent3 = self.agent3
        list_query = [state["agent2_output"].get("cau_hoi_tang_cuong", "")] + state["agent2_output"].get("cau_hoi_phan_ra", [])
        self.logger.debug(f"List of Queries for Agent3: {list_query}")

        try:
            state["retrieved_nodes"] = agent3.run(list_query=list_query, original_query=state["query"])
            state["agent3_output"] = state["retrieved_nodes"]
            self.logger.info(f"Agent3 Retrieved Nodes: {state['retrieved_nodes']}")
            state["intermediate_steps"].append("Agent3 (Retrieval) completed.")
        except Exception as e:
            self.logger.error(f"Agent3 encountered an error: {e}")
            raise e
        return state

    def agent4_node(self, state: AgentState) -> AgentState:
        self.logger.info("Starting Agent4 (Final Answer).")
        difficulty = state["agent2_output"].get("do_kho", "Trung bình")
        params = {
            "Dễ": (3, 0.5, 2),
            "Trung bình": (5, 0.5, 3),
            "Khó": (8, 0.7, 5)
        }
        _, _, top_n = params.get(difficulty, (5, 0.5, 3))
        self.logger.debug(f"Final Answer Parameters - Top N: {top_n}")

        agent4 = self.agent4
        try:
            state["final_answer_state"] = agent4.run(
                query=state["query"],
                retrieved_nodes=state["retrieved_nodes"],
            )
            state["agent4_output"] = state["final_answer_state"]
            self.logger.info(f"Agent4 Output: {state['final_answer_state']}")
            state["intermediate_steps"].append("Agent4 (Final Answer) completed.")
        except Exception as e:
            self.logger.error(f"Agent4 encountered an error: {e}")
            raise e
        return state

    def agent5_node(self, state: AgentState) -> AgentState:
        self.logger.info("Starting Agent5.")
        final_content_context = state["final_answer_state"]
        agent5 = self.agent5
        try:
            state["agent5_output"] = agent5.run(state["query"], str(final_content_context))
            self.logger.info(f"Agent5 Output: {state['agent5_output']}")
            # Set the recursion check based on Agent5's output
            state["recursive_check"] = state["agent5_output"].get('recursive', False)
            self.logger.debug(f"Recursive Check Flag: {state['recursive_check']}")
            state["intermediate_steps"].append("Agent5 completed.")
        except Exception as e:
            self.logger.error(f"Agent5 encountered an error: {e}")
            raise e
        return state

    def agent6_node(self, state: AgentState) -> AgentState:
        self.logger.info("Starting Agent6.")
        # Trích xuất doc_numbers từ agent5_output
        doc_numbers = state.get("agent5_output", {}).get("doc_numbers", [])
        contexts = state.get("agent4_output", {}).get("contexts", [[]])

        if not doc_numbers or not contexts or not contexts[0]:
            logging.warning("doc_numbers or contexts is empty.")
        else:
            extracted_texts = []
            for context in contexts:
                print(context[0])
                doc_id = context[0]  # Trích xuất ID văn bản
                doc_content = context[1]  # Trích xuất nội dung văn bản
                
                # Kiểm tra nếu doc_id nằm trong danh sách doc_numbers
                if doc_id in doc_numbers:
                    extracted_texts.append(f"{doc_content}")
        extracted_text_str = "\n".join(extracted_texts)
        self.logger.debug(f"Relevant Laws: {extracted_text_str}")
        response_2 = state.get("agent2_output", {})
        self.logger.debug(f"Response 2 Content: {response_2}")

        agent6 = self.agent6
        try:
            result = agent6.run(state["query"], str(response_2), str(extracted_text_str))
            state["agent6_output"] = result
            self.logger.info(f"Agent6 Output: {state['agent6_output']}")
            state["intermediate_steps"].append("Agent6 completed.")
            # Update final_answer_state with Agent6's output
            state["final_answer_state"] = result
            self.logger.debug(f"Updated Final Answer State: {state['final_answer_state']}")
        except Exception as e:
            self.logger.error(f"Agent6 encountered an error: {e}")
            raise e
        return state

    def _create_graph(self) -> StateGraph:
        self.logger.info("Creating LangGraph workflow.")
        workflow = StateGraph(AgentState)

        def combined_route(state: AgentState) -> str:
            relate_legal = state["agent1_output"].get("lien_quan_luat", "Không")
            retrieval_analysis = state["agent1_output"].get("can_them_thong_tin", "Không")
            self.logger.debug(f"Routing Decision - Relate Legal: {relate_legal}, Retrieval Analysis: {retrieval_analysis}")

            if relate_legal == "Có" and retrieval_analysis == "Có":
                self.logger.info("Routing to Agent2 (Retrieval).")
                return "agent2"
            elif relate_legal == "Có" and retrieval_analysis == "Không":
                self.logger.info("Routing directly to Agent6.")
                return "agent6"
            else:
                self.logger.info("Routing to END.")
                return END

        # Add nodes
        workflow.add_node("agent1", self.agent1_node)
        workflow.add_node("agent2", self.agent2_node)
        workflow.add_node("agent3", self.retrieval_node)
        workflow.add_node("agent4", self.agent4_node)
        workflow.add_node("agent5", self.agent5_node)
        workflow.add_node("agent6", self.agent6_node)

        # Start with Agent1
        workflow.add_edge(START, "agent1")
        self.logger.debug("Added edge from START to Agent1.")

        # Conditional routing after Agent1
        workflow.add_conditional_edges(
            "agent1",
            combined_route,
            {
                "agent2": "agent2",
                "agent6": "agent6",
                END: END
            }
        )
        self.logger.debug("Added conditional edges after Agent1.")

        workflow.add_edge("agent2", "agent3")
        workflow.add_edge("agent3", "agent4")
        workflow.add_edge("agent4", "agent5")

        # Conditional routing after Agent5 based on recursion
        def recursion_route(state: AgentState) -> str:
            if state.get("recursive_check"):
                self.logger.info("Recursion needed. Routing back to Agent2.")
                return "agent2"  # Re-running Agent2 as per recursion
            else:
                self.logger.info("No recursion. Routing to Agent6.")
                return "agent6"

        workflow.add_conditional_edges(
            "agent5",
            recursion_route,
            {
                "agent2": "agent2",
                "agent6": "agent6"
            }
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
            "final_answer_state": "Câu hỏi của bạn không liên quan đến các vấn đề về pháp luật, bạn có muốn đặt một câu hỏi khác không 😊",
            "intermediate_steps": [],
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
        default="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",
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
