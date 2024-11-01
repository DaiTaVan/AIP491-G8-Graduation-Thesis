from pydantic import BaseModel
from abc import abstractmethod
from typing import Dict
from openai import OpenAI as OpenAIClient
from llama_index.core.llms.llm import LLM

class BaseLLM:
    @abstractmethod
    def generate(self, **kwargs):
        """
        function to generate
        """

class OpenAI(BaseLLM):
    def __init__(
            self,
            api_key: str,
            model_name: str = 'gpt-4o-mini',
            temperature = 0.1
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.client = OpenAIClient(api_key=self.api_key)
    
    def generate(self, query):

        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": query}
                ],
            temperature = self.temperature
            )
        return completion.choices[0].message.content