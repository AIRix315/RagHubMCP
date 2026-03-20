"""Tests for LLM Provider base class.

Tests the default implementations of stream, astream, chat, and achat methods.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class MockLLMProvider:
    """Mock LLM provider implementation for testing base class behavior."""
    
    NAME = "mock-llm"
    
    def __init__(self, response: str = "test response"):
        self._response = response
        self.generate_call_count = 0
        self.last_generate_kwargs: dict[str, Any] = {}
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any
    ) -> str:
        """Mock generate implementation."""
        self.generate_call_count += 1
        self.last_generate_kwargs = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        return self._response
    
    async def agenerate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any
    ) -> str:
        """Mock async generate implementation."""
        await asyncio.sleep(0)  # Simulate async
        self.generate_call_count += 1
        return self._response
    
    def stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any
    ) -> Any:
        """Mock stream implementation - yields chunks."""
        yield self._response[:5]
        yield self._response[5:]
    
    async def astream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any
    ) -> Any:
        """Mock async stream implementation."""
        for chunk in self._response.split():
            yield chunk
            await asyncio.sleep(0)
    
    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "MockLLMProvider":
        """Create from config."""
        return cls(response=config.get("response", "default response"))


class TestLLMBaseStreamMethods:
    """Tests for streaming methods in BaseLLMProvider."""
    
    def test_stream_yields_single_chunk_default(self):
        """Test that default stream yields single chunk from generate."""
        from providers.llm.base import BaseLLMProvider
        
        # Create a concrete implementation for testing
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def __init__(self):
                self._generate_called = False
            
            def generate(self, prompt: str, temperature: float = 0.7, 
                        max_tokens: int = 1024, **kwargs) -> str:
                self._generate_called = True
                return "generated text"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        chunks = list(provider.stream("test prompt"))
        
        assert len(chunks) == 1
        assert chunks[0] == "generated text"
        assert provider._generate_called
    
    def test_stream_passes_all_parameters(self):
        """Test that stream passes all parameters to generate."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def __init__(self):
                self.last_args = {}
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                self.last_args = {
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "kwargs": kwargs
                }
                return "result"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        list(provider.stream("prompt", temperature=0.5, max_tokens=500, custom="value"))
        
        assert provider.last_args["prompt"] == "prompt"
        assert provider.last_args["temperature"] == 0.5
        assert provider.last_args["max_tokens"] == 500
        assert provider.last_args["kwargs"]["custom"] == "value"


class TestLLMBaseAsyncStreamMethods:
    """Tests for async streaming methods in BaseLLMProvider."""
    
    @pytest.mark.asyncio
    async def test_astream_yields_from_sync_stream(self):
        """Test that astream wraps sync stream correctly."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                return "full response"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        chunks = []
        async for chunk in provider.astream("test prompt"):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert chunks[0] == "full response"
    
    @pytest.mark.asyncio
    async def test_astream_yields_control_to_event_loop(self):
        """Test that astream yields control to event loop between chunks."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def stream(self, prompt: str, temperature: float = 0.7,
                      max_tokens: int = 1024, **kwargs):
                yield "chunk1"
                yield "chunk2"
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                return "result"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        chunks = []
        async for chunk in provider.astream("test"):
            chunks.append(chunk)
        
        assert chunks == ["chunk1", "chunk2"]


class TestLLMBaseChatMethods:
    """Tests for chat-style interaction methods."""
    
    def test_chat_formats_messages_into_prompt(self):
        """Test that chat formats messages into a single prompt."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def __init__(self):
                self.last_prompt = ""
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                self.last_prompt = prompt
                return "response"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"},
        ]
        
        result = provider.chat(messages)
        
        assert result == "response"
        assert "[system]: You are helpful." in provider.last_prompt
        assert "[user]: Hello!" in provider.last_prompt
    
    def test_chat_handles_missing_role(self):
        """Test that chat handles messages without role."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def __init__(self):
                self.last_prompt = ""
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                self.last_prompt = prompt
                return "response"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        messages = [
            {"content": "Just content"},
            {"role": "user", "content": "With role"},
        ]
        
        result = provider.chat(messages)
        
        assert result == "response"
        assert "[user]: Just content" in provider.last_prompt
        assert "[user]: With role" in provider.last_prompt
    
    def test_chat_handles_missing_content(self):
        """Test that chat handles messages without content."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def __init__(self):
                self.last_prompt = ""
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                self.last_prompt = prompt
                return "response"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        messages = [
            {"role": "user"},
            {"role": "assistant", "content": "Hi"},
        ]
        
        result = provider.chat(messages)
        
        assert result == "response"
        assert "[user]:" in provider.last_prompt
    
    def test_chat_passes_parameters(self):
        """Test that chat passes temperature and max_tokens."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def __init__(self):
                self.last_args = {}
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                self.last_args = {"temperature": temperature, "max_tokens": max_tokens}
                return "response"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        provider.chat([{"role": "user", "content": "Hi"}], 
                     temperature=0.3, max_tokens=200)
        
        assert provider.last_args["temperature"] == 0.3
        assert provider.last_args["max_tokens"] == 200
    
    def test_chat_passes_additional_kwargs(self):
        """Test that chat passes additional kwargs to generate."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def __init__(self):
                self.last_kwargs = {}
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                self.last_kwargs = kwargs
                return "response"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        provider.chat([{"role": "user", "content": "Hi"}], 
                     top_p=0.9, frequency_penalty=0.5)
        
        assert provider.last_kwargs["top_p"] == 0.9
        assert provider.last_kwargs["frequency_penalty"] == 0.5


class TestLLMBaseAsyncChatMethods:
    """Tests for async chat method."""
    
    @pytest.mark.asyncio
    async def test_achat_wraps_sync_chat(self):
        """Test that achat wraps sync chat using asyncio.to_thread."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                return "async response"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        messages = [{"role": "user", "content": "Hello"}]
        
        result = await provider.achat(messages)
        
        assert result == "async response"
    
    @pytest.mark.asyncio
    async def test_achat_passes_all_parameters(self):
        """Test that achat passes all parameters correctly."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def __init__(self):
                self.last_args = {}
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                self.last_args = {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "kwargs": kwargs
                }
                return "response"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        messages = [{"role": "user", "content": "Test"}]
        
        await provider.achat(messages, temperature=0.4, max_tokens=300, custom="val")
        
        assert provider.last_args["temperature"] == 0.4
        assert provider.last_args["max_tokens"] == 300
        assert provider.last_args["kwargs"]["custom"] == "val"


class TestLLMBaseAsyncGenerate:
    """Tests for async generate method."""
    
    @pytest.mark.asyncio
    async def test_agenerate_wraps_sync_generate(self):
        """Test that agenerate wraps sync generate using asyncio.to_thread."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def __init__(self):
                self.generate_called = False
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                self.generate_called = True
                return "async generated"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        result = await provider.agenerate("test prompt")
        
        assert result == "async generated"
        assert provider.generate_called
    
    @pytest.mark.asyncio
    async def test_agenerate_passes_parameters(self):
        """Test that agenerate passes all parameters."""
        from providers.llm.base import BaseLLMProvider
        
        class TestLLM(BaseLLMProvider):
            NAME = "test-llm"
            
            def __init__(self):
                self.last_args = {}
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                self.last_args = {
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "kwargs": kwargs
                }
                return "result"
            
            @classmethod
            def from_config(cls, config: dict) -> "TestLLM":
                return cls()
        
        provider = TestLLM()
        await provider.agenerate("prompt", temperature=0.2, max_tokens=100, extra="x")
        
        assert provider.last_args["prompt"] == "prompt"
        assert provider.last_args["temperature"] == 0.2
        assert provider.last_args["max_tokens"] == 100
        assert provider.last_args["kwargs"]["extra"] == "x"


class TestLLMBaseFromConfig:
    """Tests for from_config abstract method."""
    
    def test_from_config_is_abstract(self):
        """Test that from_config is an abstract method."""
        from providers.llm.base import BaseLLMProvider
        from abc import ABC
        
        # Verify that BaseLLMProvider is abstract
        assert hasattr(BaseLLMProvider, '__abstractmethods__')
        assert 'from_config' in BaseLLMProvider.__abstractmethods__
    
    def test_from_config_implementation(self):
        """Test a proper from_config implementation."""
        from providers.llm.base import BaseLLMProvider
        
        class ConfigurableLLM(BaseLLMProvider):
            NAME = "configurable-llm"
            
            def __init__(self, model: str, api_key: str = None):
                self._model = model
                self._api_key = api_key
            
            def generate(self, prompt: str, temperature: float = 0.7,
                        max_tokens: int = 1024, **kwargs) -> str:
                return f"Model {self._model} says: {prompt}"
            
            @classmethod
            def from_config(cls, config: dict) -> "ConfigurableLLM":
                return cls(
                    model=config["model"],
                    api_key=config.get("api_key")
                )
        
        config = {"model": "gpt-4", "api_key": "sk-test"}
        provider = ConfigurableLLM.from_config(config)
        
        assert provider._model == "gpt-4"
        assert provider._api_key == "sk-test"