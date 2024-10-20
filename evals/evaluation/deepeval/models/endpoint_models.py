import abc
from abc import ABC, abstractmethod
import time
import requests
from requests.exceptions import RequestException
from aiohttp import ClientSession, TCPConnector
from typing import Optional, Tuple, List, Union
from functools import cached_property
from deepeval.models.gpt_model import GPTModel

class TGIEndpointModel(GPTModel):
    def __init__(self, model: str, model_name: Optional[str] = None):
        model_name = (
            "server-endpoint"
            if model_name is None
            else model_name
        )
        super().__init__(model_name=model_name)

        self.model = model

    def _create_payload(self, prompt: str):
        return {"inputs": prompt, "parameters": {"do_sample": False}}

    @cached_property
    def header(self) -> dict:
        """Override this property to return the headers for the API request."""
        return {"Content-Type": "application/json"}

    def generate(self, prompt: str) -> Tuple[str, float]:

        try:
            start_time = time.perf_counter()
            res = requests.post(
                f"{self.model}",
                headers=self.header,
                json=self._create_payload(prompt),
            )
            res.raise_for_status()
            res = res.json()
            cost = time.perf_counter() - start_time
        except RequestException as e:
            raise Exception(f"An unexpected error occurred: {str(e)}")

        return res["generated_text"], cost 

    def load_model(self, *args, **kwargs):
        """Loads a model, that will be responsible for scoring.

        Returns:
            A model object
        """
        pass

    async def a_generate(self, prompt: str) -> Tuple[str, float]:

        try:
            start_time = time.perf_counter()
            async with ClientSession() as session:
                async with session.post(
                    f"{self.model}",
                    headers=self.header,
                    json=self._create_payload(prompt),
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        print(f"API request failed with error message: {error_text}. Retrying...")

                    response.raise_for_status()
                    res = await response.json()
            cost = time.perf_counter() - start_time
        except RequestException as e:
            raise Exception(f"An unexpected error occurred: {str(e)}")

        return res["generated_text"], cost

    def get_model_name(self, *args, **kwargs) -> str:
        return "remote endpoint"
