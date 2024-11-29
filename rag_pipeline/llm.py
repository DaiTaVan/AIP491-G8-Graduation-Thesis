from pydantic import BaseModel
from abc import abstractmethod
from typing import Dict
from openai import OpenAI as OpenAIClient
from llama_index.core.llms.llm import LLM
import requests

class BaseLLM:
    @abstractmethod
    def generate(self, **kwargs):
        """
        function to generate
        """
    
    @abstractmethod
    def chat(self, **kwargs):
        """
        function to chat
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

    def chat(self, list_message_dict):
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=list_message_dict,
            temperature = self.temperature
            )
        return completion.choices[0].message.content

class Qwen(BaseLLM):
    def __init__(
            self, 
            url: str = "http://localhost:9999/generate",
            temperature: float = 1.5,
            top_p: float = 0.1,
            max_new_tokens: int = 4096,
            timeout = 300
    ):
        self.url = url
        self.temperature = temperature
        self.top_p = top_p
        self.max_new_tokens = max_new_tokens
        self.timeout = timeout
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }

    def generate(self, query):

        data = {
            "messages": [{"role": "user", "content":query}],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_new_tokens": self.max_new_tokens
        }
        print(data)
        response = requests.post(self.url, headers=self.headers, json=data, timeout=self.timeout).json()

        return response['answer']

    def chat(self, list_message_dict):
        data = {
            "messages": list_message_dict,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_new_tokens": self.max_new_tokens
        }
        response = requests.post(self.url, headers=self.headers, json=data).json()

        return response['answer']
