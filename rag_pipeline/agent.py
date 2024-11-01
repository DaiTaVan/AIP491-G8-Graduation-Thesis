from typing import Dict
from abc import abstractmethod
from llm import BaseLLM


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
        return completion_result