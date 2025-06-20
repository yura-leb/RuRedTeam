from typing import List, Any, Optional, Union, Dict, Type
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import BaseLLM
from models.base_model import Model
from dotenv import load_dotenv
import os
from typing import AsyncGenerator
import asyncio
from tqdm import tqdm
from abc import abstractmethod

from uuid import UUID
from langchain_core.callbacks import BaseCallbackHandler
from langchain.schema import LLMResult

class LangchainModel(Model):
    """
    Generic LangChain language model wrapper.
    Provides synchronous and asynchronous methods for single and batch requests.
    Can be used with any LangChain model implementation.
    
    This is an abstract base class. Child classes only need to implement the __init__ method
    to configure the specific LangChain model they're wrapping.
    """
    
    @abstractmethod
    def __init__(self, model_name: str, batch_size: int = 0, **kwargs):
        """
        Initialize the LangChain model wrapper.
        
        Args:
            model_name: Name/identifier of the model
            batch_size: Maximum number of concurrent requests (0 for unlimited)
            **kwargs: Additional keyword arguments for the model
            
        Note:
            Child classes must implement this method to initialize:
            - self.model_name = model_name
            - self.batch_size = batch_size
            - self.kwargs = kwargs
            - self.client = <the actual LangChain model instance>
        """
        pass
    
    def invoke(self, prompt: Union[str, List[Dict[str, str]]]) -> dict:
        """
        Send a single request to the model synchronously.
        
        Args:
            prompt: A string or list of messages to send to the model
            
        Returns:
            The model's response
        """
        return dict(self.client.invoke(prompt))
    
    async def ainvoke(self, prompt: Union[str, List[Dict[str, str]]]) -> dict:
        """
        Send a single request to the model asynchronously.
        
        Args:
            prompt: A string or list of messages to send to the model
            
        Returns:
            The model's response
        """
        return dict(await self.client.ainvoke(prompt))
    
    def batch(self, prompts: List[Union[str, List[Dict[str, str]]]]) -> List[dict]:
        """
        Send multiple requests to the model synchronously.
        
        Args:
            prompts: A list of prompts to send to the model
            
        Returns:
            A list of model responses
        """
        if self.batch_size == 0:
            return [dict(response) for response in self.client.batch(prompts)]
        else:
            return [dict(response) for response in self.client.batch(prompts, config={"max_concurrency": self.batch_size})]
    
    async def abatch(self, prompts: List[Union[str, List[Dict[str, str]]]]) -> List[dict]:
        """
        Send multiple requests to the model asynchronously.
        
        Args:
            prompts: A list of prompts to send to the model
            
        Returns:
            A list of model responses
        """
        if self.batch_size == 0:
            with BatchCallback(len(prompts)) as cb:
                return [dict(response) for response in await self.client.abatch(prompts, config={"callbacks": [cb]})]
        else:
            with BatchCallback(len(prompts)) as cb:
                return [dict(response) for response in await self.client.abatch(prompts, config={"max_concurrency": self.batch_size, "callbacks": [cb]})]

    def is_answer_blocked(self, answer: dict) -> bool:
        """
        Check if the answer is blocked by guardrails.
        Different LangChain models may have different mechanisms for indicating blocked responses.
        
        Returns:
            Boolean indicating if the answer was blocked
        """
        if "response_metadata" in answer and "finish_reason" in answer["response_metadata"]:
            return answer["response_metadata"]["finish_reason"] == "blacklist"
        return False

    def get_params(self) -> dict:
        """
        Get the parameters of the model.
        
        Returns:
            Dictionary with model parameters
        """
        return {
            **self.client.dict(),
            "batch_size": self.batch_size
        }
    
    async def stream_abatch(self, prompts: List[Union[str, List[Dict[str, str]]]], batch_size: int = 1) -> AsyncGenerator[dict, None]:
        """
        Send multiple requests to the model asynchronously and yield results as they complete.
        
        Args:
            prompts: A list of prompts to send to the model
            batch_size: Number of prompts to process concurrently
        
        Returns:
            An async generator of model responses in order of completion
        """
        semaphore = asyncio.Semaphore(batch_size)
        async def sem_task(idx, prompt):
            async with semaphore:
                result = await self.ainvoke(prompt)
                return idx, result

        tasks = [asyncio.create_task(sem_task(i, inp)) for i, inp in enumerate(prompts)]
        total_tasks = len(tasks)
        
        results = dict()
        cur_result_idx = 0
        
        # Create tqdm progress bar
        progress_bar = tqdm(total=total_tasks, desc=f"Processing requests with {self.model_name}", unit="request")

        for task in asyncio.as_completed(tasks):
            idx, res = await task
            progress_bar.update(1)  # Update progress bar for each completed task

            results[idx] = res
            while cur_result_idx in results:
                yield dict(results[cur_result_idx])
                results.pop(cur_result_idx)
                cur_result_idx += 1

        progress_bar.close()  # Close the progress bar when done 


class BatchCallback(BaseCallbackHandler):
    def __init__(self, total: int):
        super().__init__()
        self.count = 0
        self.progress_bar = tqdm(total=total)  # define a progress bar
        
    # Override on_llm_end method. This is called after every response from LLM
    def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        self.count += 1
        self.progress_bar.update(1)
        
    def __enter__(self):
        self.progress_bar.__enter__()
        return self
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.progress_bar.__exit__(exc_type, exc_value, exc_traceback)
        
    def __del__(self):
        self.progress_bar.__del__()