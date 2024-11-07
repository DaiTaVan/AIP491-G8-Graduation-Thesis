from typing import Any, Dict, List

from vector_database import NodeWithScore
from llm import OpenAI

RANKGPT_RERANK_PROMPT = (
    "Search Query: {query}. \nRank the {num} passages above "
    "based on their relevance to the search query. The passages "
    "should be listed in descending order using identifiers. "
    "The most relevant passages should be listed first. "
    "The unrelevant passages should be removed"
    "The output format should be [] > [], e.g., [1] > [2]. "
    "Only response the ranking results, "
    "do not say any word or explain."
)

class RankGPTRerank:
    """RankGPT-based reranker."""

    def __init__(
        self,
        top_n: int = 5,
        llm: OpenAI = None,
        verbose: bool = False,
        rankgpt_rerank_prompt: str = None,
    ):
        self.top_n = top_n
        self.llm = llm
        self.verbose = verbose
        self.rankgpt_rerank_prompt = rankgpt_rerank_prompt or RANKGPT_RERANK_PROMPT
        
    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query: str,
    ) -> List[NodeWithScore]:

        items = {
            "query": query,
            "hits": [
                {"content": node["metadata"]["content"]}
                for node in nodes
            ],
        }

        messages = self.create_permutation_instruction(item=items)
        permutation = self.run_llm(messages=messages)

        rerank_ranks = self._receive_permutation(
            items, permutation
        )
        if self.verbose:
            print(f"After Reranking, new rank list for nodes: {rerank_ranks}")

        initial_results: List[NodeWithScore] = []

        for idx in rerank_ranks:
            initial_results.append(
                nodes[idx]
            )

        return initial_results[: self.top_n]

    def _get_prefix_prompt(self, query: str, num: int) -> List[Dict]:
        return [
            {
                "role": "system",
                "content": "You are RankGPT, an intelligent assistant that can rank passages based on their relevancy to the query.",
            },
            {
                "role": "user",
                "content": f"I will provide you with {num} passages, each indicated by number identifier []. \nRank the passages based on their relevance to query: {query}.",
            },
            {
                "role": "assistant", 
                "content": "Okay, please provide the passages."
            },
        ]

    def _get_post_prompt(self, query: str, num: int) -> str:
        return self.rankgpt_rerank_prompt.format(query=query, num=num)

    def create_permutation_instruction(self, item: Dict[str, Any]) -> List[Dict]:
        query = item["query"]
        num = len(item["hits"])

        messages = self._get_prefix_prompt(query, num)
        rank = 0
        for hit in item["hits"]:
            rank += 1
            content = hit["content"]
            content = content.strip()
            messages.append({"role":"user", "content":f"[{rank}] {content}"})
            messages.append(
                {"role": "assistant", "content": f"Received passage [{rank}]."}
            )
        messages.append(
            {"role": "user", "content": self._get_post_prompt(query, num)}
        )
        return messages

    def run_llm(self, messages: List[Dict]) -> str:
        return self.llm.chat(messages)

    def _clean_response(self, response: str) -> str:
        new_response = ""
        for c in response:
            if not c.isdigit():
                new_response += " "
            else:
                new_response += c
        return new_response.strip()

    def _remove_duplicate(self, response: List[int]) -> List[int]:
        new_response = []
        for c in response:
            if c not in new_response:
                new_response.append(c)
        return new_response

    def _receive_permutation(self, item: Dict[str, Any], permutation: str) -> List[int]:
        rank_end = len(item["hits"])

        response = self._clean_response(permutation)
        response_list = [int(x) - 1 for x in response.split()]
        response_list = self._remove_duplicate(response_list)
        response_list = [ss for ss in response_list if ss in range(rank_end)]
        return response_list + [
            tt for tt in range(rank_end) if tt not in response_list
        ]  # add the rest of the rank
