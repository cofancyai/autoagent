"""LLM API client supporting Anthropic and OpenRouter"""

import json
import logging
import time
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from anthropic import AsyncAnthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)


class Provider(str, Enum):
    """LLM Provider types"""

    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"


class ModelType(str, Enum):
    """Claude model types"""

    OPUS = "opus"
    SONNET = "sonnet"
    HAIKU = "haiku"


class AnthropicClient:
    """Client for LLM APIs (Anthropic Claude and OpenRouter)"""

    # OpenRouter API endpoint
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    # Model configurations
    MODEL_CONFIG = {
        ModelType.OPUS: {
            "id": "claude-opus-4-20250514",
            "max_tokens": 8192,
            "temperature": 0.7,
            "use_cases": ["deep_research", "complex_reasoning", "architecture"],
        },
        ModelType.SONNET: {
            "id": "claude-sonnet-4-5-20250929",
            "max_tokens": 8192,
            "temperature": 0.7,
            "use_cases": ["code_generation", "planning", "approvals"],
        },
        ModelType.HAIKU: {
            "id": "claude-haiku-4-20250514",
            "max_tokens": 4096,
            "temperature": 0.5,
            "use_cases": ["quick_reply", "simple_tasks", "status"],
        },
    }

    def __init__(self):
        """Initialize LLM client (auto-detects provider from API key)"""
        self.api_key = settings.anthropic_api_key
        self.enable_caching = settings.llm_enable_prompt_caching

        # Detect provider from API key format
        self.provider = self._detect_provider(self.api_key)

        # Log provider detection
        masked_key = (
            f"{self.api_key[:10]}...{self.api_key[-4:]}" if len(self.api_key) > 14 else "***"
        )
        logger.info(f"Initializing LLM client - Provider: {self.provider.value}")
        logger.debug(f"API Key (masked): {masked_key}")

        # Initialize appropriate client
        if self.provider == Provider.ANTHROPIC:
            logger.info("Using Anthropic Claude API")
            self.client = AsyncAnthropic(api_key=self.api_key)
            self.http_client = None
        else:  # OpenRouter
            logger.info(f"Using OpenRouter API - Base URL: {self.OPENROUTER_BASE_URL}")
            logger.info(f"OpenRouter Model: {settings.openrouter_model}")
            self.client = None
            self.http_client = httpx.AsyncClient(
                base_url=self.OPENROUTER_BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/cofancyai/autoagent",
                    "X-Title": "ThinkingAgent",
                },
                timeout=60.0,
            )
            logger.debug("HTTP Client initialized with timeout: 60.0s")

    def _detect_provider(self, api_key: str) -> Provider:
        """Detect LLM provider from API key format"""
        if api_key.startswith("sk-or-v1-"):
            return Provider.OPENROUTER
        return Provider.ANTHROPIC

    def _get_model_id(self, model_type: ModelType) -> str:
        """Get model ID from model type"""
        if self.provider == Provider.OPENROUTER:
            # Use OpenRouter model from settings
            return settings.openrouter_model
        return self.MODEL_CONFIG[model_type]["id"]

    def _get_model_config(self, model_type: ModelType) -> Dict[str, Any]:
        """Get model configuration"""
        return self.MODEL_CONFIG[model_type]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
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
        Generate a response from LLM (supports both Anthropic and OpenRouter)

        Args:
            model: Model type to use
            messages: List of messages in the conversation
            system_context: System context/prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            use_cache: Enable prompt caching (Anthropic only)
            stream: Enable response streaming

        Returns:
            Dict containing response, usage info, and metadata
        """
        if self.provider == Provider.ANTHROPIC:
            return await self._generate_anthropic(
                model, messages, system_context, max_tokens, temperature, use_cache, stream
            )
        else:  # OpenRouter
            return await self._generate_openrouter(
                model, messages, system_context, max_tokens, temperature, stream
            )

    async def _generate_anthropic(
        self,
        model: ModelType,
        messages: List[Dict[str, str]],
        system_context: Optional[str],
        max_tokens: Optional[int],
        temperature: Optional[float],
        use_cache: bool,
        stream: bool,
    ) -> Dict[str, Any]:
        """Generate response using Anthropic API"""
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
                    {"type": "text", "text": system_context, "cache_control": {"type": "ephemeral"}}
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

    async def _generate_openrouter(
        self,
        model: ModelType,
        messages: List[Dict[str, str]],
        system_context: Optional[str],
        max_tokens: Optional[int],
        temperature: Optional[float],
        stream: bool,
    ) -> Dict[str, Any]:
        """Generate response using OpenRouter API (OpenAI-compatible format)"""
        logger.info("=" * 80)
        logger.info("OpenRouter API Call Starting")
        logger.info("=" * 80)

        start_time = time.time()

        model_config = self._get_model_config(model)
        model_id = self._get_model_id(model)  # Gets OpenRouter model

        # Use provided values or defaults from config
        max_tokens = max_tokens or model_config["max_tokens"]
        temperature = temperature or model_config["temperature"]

        logger.info(f"Model Type: {model.value}")
        logger.info(f"Model ID: {model_id}")
        logger.info(f"Max Tokens: {max_tokens}")
        logger.info(f"Temperature: {temperature}")

        # Build OpenAI-compatible messages format
        openai_messages = []

        # Add system message if provided
        if system_context:
            logger.debug(f"System Context Length: {len(system_context)} chars")
            logger.debug(f"System Context Preview: {system_context[:200]}...")
            openai_messages.append({"role": "system", "content": system_context})

        # Add conversation messages
        logger.debug(f"Number of messages: {len(messages)}")
        for i, msg in enumerate(messages):
            logger.debug(
                f"Message {i}: role={msg.get('role')}, content_length={len(msg.get('content', ''))}"
            )
        openai_messages.extend(messages)

        # Build request payload
        payload = {
            "model": model_id,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Log request details
        logger.info(f"API Endpoint: {self.OPENROUTER_BASE_URL}/chat/completions")
        logger.debug(f"Request Headers: {self._mask_headers()}")
        logger.debug(f"Request Payload: {json.dumps(payload, indent=2)[:500]}...")

        try:
            # Make API call to OpenRouter
            logger.info("Sending request to OpenRouter...")
            response = await self.http_client.post("/chat/completions", json=payload)

            logger.info(f"Response Status Code: {response.status_code}")
            logger.debug(f"Response Headers: {dict(response.headers)}")

            # Log response body before raising for status
            response_text = response.text
            logger.debug(f"Response Body: {response_text[:1000]}")

            response.raise_for_status()
            data = response.json()

            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Request completed successfully in {latency_ms}ms")

            # Extract response in same format as Anthropic
            content = ""
            if data.get("choices") and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                logger.debug(f"Response Content Length: {len(content)} chars")
                logger.debug(f"Response Preview: {content[:200]}...")

            usage = data.get("usage", {})
            logger.info(
                f"Token Usage - Prompt: {usage.get('prompt_tokens', 0)}, "
                f"Completion: {usage.get('completion_tokens', 0)}, "
                f"Total: {usage.get('total_tokens', 0)}"
            )

            finish_reason = (
                data["choices"][0].get("finish_reason", "stop") if data.get("choices") else "stop"
            )

            logger.info("=" * 80)
            return {
                "content": content,
                "model": model_id,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                "latency_ms": latency_ms,
                "stop_reason": finish_reason,
            }

        except httpx.HTTPStatusError as e:
            logger.error("=" * 80)
            logger.error(f"HTTP Error: {e.response.status_code}")
            logger.error(f"Response Body: {e.response.text}")
            logger.error(f"Request URL: {e.request.url}")
            logger.error(f"Request Headers: {self._mask_headers()}")
            logger.error("=" * 80)
            raise
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"Unexpected Error: {type(e).__name__}: {str(e)}")
            logger.error("=" * 80)
            raise

    def _mask_headers(self) -> Dict[str, str]:
        """Return headers with masked API key for logging"""
        if self.http_client and hasattr(self.http_client, "headers"):
            headers = dict(self.http_client.headers)
            if "Authorization" in headers:
                auth = headers["Authorization"]
                if "Bearer " in auth:
                    key = auth.replace("Bearer ", "")
                    headers["Authorization"] = f"Bearer {key[:10]}...{key[-4:]}"
            return headers
        return {}

    async def _stream_response(
        self, request_params: Dict[str, Any], start_time: float
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
        self, model: ModelType, prompt_tokens: int, completion_tokens: int
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
        # OpenRouter free models have no cost
        if self.provider == Provider.OPENROUTER:
            return 0.0

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
            },
        }

        model_pricing = pricing[model]
        prompt_cost = prompt_tokens * model_pricing["prompt"]
        completion_cost = completion_tokens * model_pricing["completion"]

        return prompt_cost + completion_cost

    async def close(self):
        """Close HTTP client connection (OpenRouter only)"""
        if self.http_client:
            await self.http_client.aclose()


# Singleton instance
anthropic_client = AnthropicClient()
