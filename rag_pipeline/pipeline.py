import json
import os
import argparse
from typing import Dict, List, TypedDict

from llm import Ollama, OpenAI
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM

from langgraph.graph import Graph, START, END
from vector_database import LawBGEM3QdrantDatabase
from embedding import BGEEmbedding
from reranker import JinaRerank, RankGPTRerank
from knowledge_graph.neo4j_database import Neo4jDatabase

from agent import Agent1, Agent2, Agent3, Agent4, Agent5, Agent6  # Ensure Agent5 & Agent6 are imported


class AgentState(TypedDict):
    query: str
    legal_topics: str
    agent1_output: Dict
    agent2_output: Dict
    retrieved_nodes: List
    final_answer_state: str
    intermediate_steps: List
    agent5_output: str
    agent6_output: str


class Pipeline:
    def __init__(
        self,
        openai_api_key: str,
        qdrant_url: str = "http://localhost:6333",
        qdrant_api_key: str = None,
        neo4j_uri: str = "neo4j://localhost",
        neo4j_auth: tuple = ("neo4j", "Abc12345"),
        config_path: str = "config/agent.json",
        legal_topics_path: str = "test.txt",
    ):
        self.openai_api_key = openai_api_key
        os.environ["OPENAI_API_KEY"] = openai_api_key

        # Initialize models
        self.gpt_model = ChatOpenAI(temperature=0.4, model_name="gpt-4o-mini")
        self.ollama_model = OllamaLLM(model="qwen:2.5", temperature=0.7)

        # Initialize database configurations
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.neo4j_uri = neo4j_uri
        self.neo4j_auth = neo4j_auth

        # Load configuration
        self.config = {}
        self.legal_topics_path = legal_topics_path
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as file:
                self.config = json.load(file)
        else:
            print(f"Config file not found at {config_path}. Using empty configuration.")

        # Create the LangGraph workflow
        self.graph = self._create_graph()

    def agent1_node(self, state: AgentState) -> AgentState:
        """Determines if the query is legal-related and its category."""
        try:
            agent1 = Agent1(config=self.config, model=self.gpt_model)
            state["agent1_output"] = agent1.run(query=state["query"])
            return state
        except Exception as e:
            print(f"Error in agent1_node: {e}")
            raise

    def agent2_node(self, state: AgentState) -> AgentState:
        """Analyzes the query and breaks it down into components."""
        try:
            question_category = state["agent1_output"].get("danh_muc_cau_hoi", "")

            # Load legal topics
            if os.path.exists(self.legal_topics_path):
                with open(self.legal_topics_path, "r", encoding="utf-8") as file:
                    legal_topics = file.read()
            else:
                print(f"Legal topics file not found at {self.legal_topics_path}. Using empty string.")
                legal_topics = ""

            input_agent2 = f"Đề mục trong văn bản pháp luật Việt Nam: {legal_topics}\nLoại câu hỏi: {question_category}"

            agent2 = Agent2(config=self.config, model=self.gpt_model)
            state["agent2_output"] = agent2.run(input_agent2=input_agent2, query=state["query"])
            return state
        except Exception as e:
            print(f"Error in agent2_node: {e}")
            raise

    def retrieval_node(self, state: AgentState) -> AgentState:
        """Retrieves relevant legal documents based on query analysis."""
        try:
            difficulty = state["agent2_output"].get("do_kho", "Trung bình")
            params = {
                "Dễ": (3, 0.5, 2),
                "Trung bình": (5, 0.5, 3),
                "Khó": (8, 0.7, 5)
            }
            top_k, alpha, top_n = params.get(difficulty, (5, 0.5, 3))

            # Initialize vector database and retriever components
            vector_database = LawBGEM3QdrantDatabase(url=self.qdrant_url, api_key=self.qdrant_api_key)
            embedding_model = BGEEmbedding(model_name="BAAI/bge-m3")
            jina_reranker = JinaRerank(
                top_n=top_n,
                model="jina-colbert-v2",
                api_key="jina_c3454a5b2f874d2290894c0d81137503mLsIhAJEVBn1SAKqFNjJbMnhQCnk"
            )

            # Prepare queries for retrieval
            list_query = [state["agent2_output"].get("cau_hoi_tang_cuong", "")] + state["agent2_output"].get("cau_hoi_phan_ra", [])
            print(f"Retrieval Queries: {list_query}")

            # Perform retrieval
            agent3 = Agent3(llm=self.gpt_model, vector_database=vector_database, embedding=embedding_model, reranker=jina_reranker)
            state["retrieved_nodes"] = agent3.run(list_query=list_query, original_query=state["query"])

            if not state["retrieved_nodes"]:
                print("No nodes retrieved in retrieval_node.")

            return state
        except Exception as e:
            print(f"Error in retrieval_node: {e}")
            raise

    def final_answer_node(self, state: AgentState) -> AgentState:
        """Generates the final answer using retrieved information."""
        try:
            difficulty = state["agent2_output"].get("do_kho", "Trung bình")
            params = {
                "Dễ": (3, 0.5, 2),
                "Trung bình": (5, 0.5, 3),
                "Khó": (8, 0.7, 5)
            }
            _, _, top_n = params.get(difficulty, (5, 0.5, 3))

            gpt_reranker = RankGPTRerank(
                top_n=top_n,
                llm=OpenAI(
                    temperature=0,
                    model_name="gpt-4o-mini"
                ),
            )
            graph_db = Neo4jDatabase(
                uri=self.neo4j_uri,
                username=self.neo4j_auth[0],
                password=self.neo4j_auth[1],
            )

            agent4 = Agent4(
                rerank=gpt_reranker,
                graph_database=graph_db,
            )
            # final_answer_state as final_content_context
            state["final_answer_state"] = agent4.run(
                query=state["query"],
                retrieved_nodes=state["retrieved_nodes"],
            )
            return state
        except Exception as e:
            print(f"Error in final_answer_node: {e}")
            raise

    def agent5_node(self, state: AgentState) -> AgentState:
        """Processes the final answer through Agent5."""
        try:
            final_content_context = state["final_answer_state"]
            agent5 = Agent5(
                model=self.gpt_model,
                config=self.config
            )
            # Run Agent5
            ans = agent5.run(state["query"], str(final_content_context))
            state["agent5_output"] = ans
            return state
        except Exception as e:
            print(f"Error in agent5_node: {e}")
            raise

    def agent6_node(self, state: AgentState) -> AgentState:
        """Processes the output through Agent6 and generates the final Markdown output."""
        try:
            final_content_context = state["final_answer_state"]
            response_2 = state["agent5_output"]  # Assuming response_2 comes from Agent5

            agent6 = Agent6(
                model=self.gpt_model,
                config=self.config
            )
            result = agent6.run(state["query"], str(response_2), str(final_content_context))
            state["agent6_output"] = result
            return state
        except Exception as e:
            print(f"Error in agent6_node: {e}")
            raise

    def _create_graph(self) -> Graph:
        """Creates the workflow graph for the pipeline."""
        workflow = Graph()
        # Add nodes
        workflow.add_node("agent1", self.agent1_node)
        workflow.add_node("agent2", self.agent2_node)
        workflow.add_node("retrieval", self.retrieval_node)
        workflow.add_node("final_answer", self.final_answer_node)
        workflow.add_node("agent5", self.agent5_node)
        workflow.add_node("agent6", self.agent6_node)

        # Add edges
        workflow.add_edge(START, "agent1")
        workflow.add_edge("agent1", "agent2")
        workflow.add_edge("agent2", "retrieval")
        workflow.add_edge("retrieval", "final_answer")
        workflow.add_edge("final_answer", "agent5")
        workflow.add_edge("agent5", "agent6")
        workflow.add_edge("agent6", END)

        return workflow.compile()

    def run(self, query: str, legal_topics: str) -> Dict:
        """Executes the pipeline."""
        try:
            state = AgentState(
                query=query,
                legal_topics=legal_topics,
                agent1_output={},
                agent2_output={},
                retrieved_nodes=[],
                final_answer_state="",  # renamed from final_answer to match your code
                intermediate_steps=[],
                agent5_output="",
                agent6_output=""
            )
            result = self.graph.invoke(state)
            return result
        except Exception as e:
            print(f"Error during pipeline run: {e}")
            raise


def main():
    # Set up argument parser with default values
    parser = argparse.ArgumentParser(description="Run the legal document pipeline with optional arguments.")

    parser.add_argument(
        "--query",
        type=str,
        default=(
            "Bố mẹ tôi có ý định cho riêng chị gái tôi (đã có chồng) một căn hộ chung cư và một số tài sản khác. "
            "Xin hỏi, bố mẹ tôi phải lập những loại giấy tờ gì để chứng minh căn hộ chung cư và "
            "tài sản trên là tài sản riêng của chị gái tôi?"
        ),
        help="Query to process through the pipeline."
    )
    parser.add_argument(
        "--config_path",
        type=str,
        default="/teamspace/studios/this_studio/AIP491-G8-Graduation-Thesis/rag_pipeline/config/agent.json",
        help="Path to the JSON configuration file for the pipeline."
    )
    parser.add_argument(
        "--legal_topics_path",
        type=str,
        default="/teamspace/studios/this_studio/AIP491-G8-Graduation-Thesis/rag_pipeline/test.txt",
        help="Path to the text file containing legal topics."
    )
    parser.add_argument(
        "--openai_api_key",
        type=str,
        default="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",
        help="OpenAI API key for accessing GPT models."
    )
    parser.add_argument(
        "--qdrant_url",
        type=str,
        default="http://localhost:6333",
        help="URL for the Qdrant vector database."
    )
    parser.add_argument(
        "--qdrant_api_key",
        type=str,
        default=None,
        help="API key for the Qdrant vector database."
    )
    parser.add_argument(
        "--neo4j_uri",
        type=str,
        default="neo4j://localhost",
        help="URI for the Neo4j database."
    )
    parser.add_argument(
        "--neo4j_auth",
        type=str,
        nargs=2,
        default=["neo4j", "Abc12345"],
        help="Authentication tuple for Neo4j database (username password)."
    )

    # Parse arguments
    args = parser.parse_args()

    # Read legal topics
    if os.path.exists(args.legal_topics_path):
        with open(args.legal_topics_path, "r", encoding="utf-8") as file:
            legal_topics = file.read()
    else:
        print(f"Legal topics file not found at {args.legal_topics_path}. Using empty string.")
        legal_topics = ""

    # Initialize pipeline
    pipeline = Pipeline(
        openai_api_key=args.openai_api_key,
        qdrant_url=args.qdrant_url,
        qdrant_api_key=args.qdrant_api_key,
        neo4j_uri=args.neo4j_uri,
        neo4j_auth=tuple(args.neo4j_auth),
        config_path=args.config_path,
        legal_topics_path=args.legal_topics_path
    )

    # Run the pipeline
    try:
        result = pipeline.run(args.query, legal_topics)
    except Exception as e:
        print(f"Pipeline execution failed: {e}")
        return

    # Print results
    print("\n--- Pipeline Results ---")
    print("Final Answer State:", result.get("final_answer_state", "No final answer"))
    print("Agent5 Output:", result.get("agent5_output", "No agent5 output"))
    print("Agent6 Output:", result.get("agent6_output", "No agent6 output"))


if __name__ == "__main__":
    main()
