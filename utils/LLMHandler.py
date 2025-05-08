from abc import ABC, abstractmethod
import os
import google.generativeai as genai
from huggingface_hub import InferenceClient
import ollama
from typing import List, Dict, Any, Optional

class BaseLLMHandler(ABC):
    """Abstract base class for LLM handlers"""
    
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response from the LLM"""
        pass

class GeminiHandler(BaseLLMHandler):
    """Handler for Google's Gemini LLM"""
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.token = os.environ.get('GEMINI_KEY')
        if not self.token:
            raise ValueError("GEMINI_KEY environment variable not set")
            
        genai.configure(api_key=self.token)
        self.model = genai.GenerativeModel(model_name)
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        prompt = f'TASK: {system_prompt}\n\nUSER INPUT: {user_prompt}'
        response = self.model.generate_content(prompt)
        print(response.usage_metadata)
        return response.text

class HuggingFaceHandler(BaseLLMHandler):
    """Handler for HuggingFace models"""

    def __init__(self, model_name: str = "Qwen/Qwen2.5-72B-Instruct"):
        self.token = os.environ.get('HF_TOKEN')
        if not self.token:
            raise ValueError("HF_TOKEN environment variable not set")

        self.client = InferenceClient(
            api_key=self.token,
            headers={"X-use-cache": "false"}
        )
        self.model_name = model_name

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=2000
        )

        return completion.choices[0].message.content


class OllamaHandler(BaseLLMHandler):
    """Handler for Ollama's local LLMs"""

    def __init__(self, model_name: str = "gemma3:1b"):
        self.model_name = model_name
        all_ollama_models = [i.model for i in ollama.list().models]

        self.pull = False
        if model_name not in all_ollama_models:
            self.pull = True

    def generate(self, system_prompt: str, user_prompt: str) -> str:

        if self.pull:
            ollama.pull(self.model_name)
            self.pull = False

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = ollama.chat(model=self.model_name, messages=messages)
        return response["message"]["content"]


class LLMHandler:
    """Main handler class that manages different LLM providers"""
    
    def __init__(self, provider: str = "gemini", model_name: Optional[str] = None):
        self.providers = {
            "gemini": lambda m: GeminiHandler(model_name=m if m else "gemini-1.5-flash"),
            "huggingface": lambda m: HuggingFaceHandler(model_name=m if m else "Qwen/Qwen2.5-72B-Instruct"),
            "ollama": lambda m: OllamaHandler(model_name=m if m else "gemma3:1b")
        }
        
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}. Available providers: {list(self.providers.keys())}")
        
        self.handler = self.providers[provider](model_name)
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using the configured LLM provider"""
        return self.handler.generate(system_prompt, user_prompt)
    
    # @classmethod
    # def register_provider(cls, name: str, handler_class: type) -> None:
    #     """Register a new LLM provider"""
    #     if not issubclass(handler_class, BaseLLMHandler):
    #         raise ValueError("Handler class must inherit from BaseLLMHandler")
    #     cls.providers[name] = lambda m: handler_class(model_name=m)
