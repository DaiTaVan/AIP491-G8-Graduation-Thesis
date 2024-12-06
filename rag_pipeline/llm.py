from pydantic import BaseModel
from abc import abstractmethod
from typing import Dict
from openai import OpenAI as OpenAIClient
from llama_index.core.llms.llm import LLM
import requests
import os
from typing import List, Dict
from dotenv import load_dotenv
# Load environment variables from the .env file
load_dotenv()
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

class Ollama(BaseLLM):
    def __init__(
        self,
        model_name: str,
        base_url: str = "http://localhost:11434",  # Default Ollama API endpoint
        temperature: float = 0.1,
    ):
        """
        Initialize the Ollama LLM.

        :param model_name: Name of the model to use.
        :param base_url: Base URL for the Ollama API.
        :param temperature: Sampling temperature.
        """
        self.model_name = model_name
        self.base_url = base_url
        self.temperature = temperature
    
    def _request(self, endpoint: str, payload: Dict) -> Dict:
        """
        Helper function to send requests to the Ollama API.

        :param endpoint: API endpoint (e.g., `/api/generate`).
        :param payload: JSON payload for the request.
        :return: JSON response.
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def generate(self, query: str) -> str:
        """
        Generate text using the Ollama model.

        :param query: Query or prompt to generate text for.
        :return: Generated text.
        """
        payload = {
            "model": self.model_name,
            "prompt": query,
            "temperature": self.temperature,
        }
        response = self._request("/api/generate", payload)
        return response.get("text", "")

    def chat(self, list_message_dict: List[Dict[str, str]]) -> str:
        """
        Chat using the Ollama model.

        :param list_message_dict: List of messages in dict format with roles and content.
        :return: Generated response.
        """
        payload = {
            "model": self.model_name,
            "messages": list_message_dict,
            "temperature": self.temperature,
        }
        response = self._request("/api/chat", payload)
        return response.get("text", "")

class OpenAI(BaseLLM):
    def __init__(
            self,
            api_key: str = os.getenv('OPENAI_API_KEY'),
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
