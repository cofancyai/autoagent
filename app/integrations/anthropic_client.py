"""Anthropic Claude API client"""

import time
from enum import Enum
from typing import Optional, List, Dict, Any, AsyncIterator
from anthropic import AsyncAnthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.config import settings


class ModelType(str, Enum):
    """Claude model types"""
    OPUS = "opus"
    SONNET = "sonnet"
    HAIKU = "haiku"


class AnthropicClient:
    """Client for Anthropic Claude API with prompt caching support"""

    # Model configurations
    MODEL_CONFIG = {
        ModelType.OPUS: {
            "id": "claude-opus-4-20250514",
            "max_tokens": 8192,
            "temperature": 0.7,
            "use_cases": ["deep_research", "complex_reasoning", "architecture"]
        },
        ModelType.SONNET: {
            "id": "claude-sonnet-4-5-20250929",
            "max_tokens": 8192,
            "temperature": 0.7,
            "use_cases": ["code_generation", "planning", "approvals"]
        },
        ModelType.HAIKU: {
            "id": "claude-haiku-4-20250514",
            "max_tokens": 4096,
            "temperature": 0.5,
            "use_cases": ["quick_reply", "simple_tasks", "status"]
        }
    }

    def __init__(self):
        """Initialize Anthropic client"""
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.enable_caching = settings.llm_enable_prompt_caching

    def _get_model_id(self, model_type: ModelType) -> str:
        """Get model ID from model type"""
        return self.MODEL_CONFIG[model_type]["id"]

    def _get_model_config(self, model_type: ModelType) -> Dict[str, Any]:
        """Get model configuration"""
        return self.MODEL_CONFIG[model_type]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def generate(
        self,
        model: ModelType,
        messages: List[Dict[str, str]],
        system_context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_cache: bool = False,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a response from Claude

        Args:
            model: Model type to use
            messages: List of messages in the conversation
            system_context: System context/prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            use_cache: Enable prompt caching
            stream: Enable response streaming

        Returns:
            Dict containing response, usage info, and metadata
        """
        start_time = time.time()

        model_config = self._get_model_config(model)
        model_id = model_config["id"]

        # Use provided values or defaults from config
        max_tokens = max_tokens or model_config["max_tokens"]
        temperature = temperature or model_config["temperature"]

        # Build request
        request_params = {
            "model": model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        # Add system context with caching if enabled
        if system_context:
            if use_cache and self.enable_caching:
                request_params["system"] = [
                    {
                        "type": "text",
                        "text": system_context,
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
            else:
                request_params["system"] = system_context

        # Make API call
        if stream:
            return await self._stream_response(request_params, start_time)
        else:
            response = await self.client.messages.create(**request_params)

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "content": response.content[0].text if response.content else "",
                "model": model_id,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                "latency_ms": latency_ms,
                "stop_reason": response.stop_reason,
            }

    async def _stream_response(
        self,
        request_params: Dict[str, Any],
        start_time: float
    ) -> AsyncIterator[str]:
        """Stream response from Claude"""
        async with self.client.messages.stream(**request_params) as stream:
            async for text in stream.text_stream:
                yield text

    async def select_model_for_task(self, task_type: str) -> ModelType:
        """
        Select the best model for a given task type

        Args:
            task_type: Type of task (e.g., 'deep_research', 'code_generation')

        Returns:
            ModelType to use for this task
        """
        task_routing = {
            "deep_research": ModelType.OPUS,
            "complex_reasoning": ModelType.OPUS,
            "architecture_design": ModelType.OPUS,
            "code_generation": ModelType.SONNET,
            "planning": ModelType.SONNET,
            "approval_presentation": ModelType.SONNET,
            "quick_reply": ModelType.HAIKU,
            "simple_task": ModelType.HAIKU,
        }

        return task_routing.get(task_type, ModelType.SONNET)

    async def estimate_cost(
        self,
        model: ModelType,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Estimate cost of an API call

        Args:
            model: Model type used
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in USD
        """
        # Anthropic pricing (as of 2025-01)
        # These are approximate and should be updated with actual pricing
        pricing = {
            ModelType.OPUS: {
                "prompt": 15.0 / 1_000_000,  # $15 per million tokens
                "completion": 75.0 / 1_000_000,  # $75 per million tokens
            },
            ModelType.SONNET: {
                "prompt": 3.0 / 1_000_000,  # $3 per million tokens
                "completion": 15.0 / 1_000_000,  # $15 per million tokens
            },
            ModelType.HAIKU: {
                "prompt": 0.25 / 1_000_000,  # $0.25 per million tokens
                "completion": 1.25 / 1_000_000,  # $1.25 per million tokens
            }
        }

        model_pricing = pricing[model]
        prompt_cost = prompt_tokens * model_pricing["prompt"]
        completion_cost = completion_tokens * model_pricing["completion"]

        return prompt_cost + completion_cost


# Singleton instance
anthropic_client = AnthropicClient()
