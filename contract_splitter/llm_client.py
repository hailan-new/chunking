"""
LLM客户端管理模块
支持多种LLM提供商的统一接口
"""

import os
import logging
import time
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """
    LLM客户端基类
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM客户端
        
        Args:
            config: LLM配置
        """
        self.config = config
        self.model = config.get("model", "gpt-3.5-turbo")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 1000)
        self.timeout = config.get("timeout", 30)
        self.retry_times = config.get("retry_times", 3)
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
            
        Returns:
            生成的文本
        """
        pass
    
    def generate_with_retry(self, prompt: str, **kwargs) -> str:
        """
        带重试的文本生成
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
            
        Returns:
            生成的文本
        """
        last_error = None
        
        for attempt in range(self.retry_times):
            try:
                return self.generate(prompt, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.retry_times - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.warning(f"LLM call failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"LLM call failed after {self.retry_times} attempts: {e}")
        
        raise last_error


class QwenClient(BaseLLMClient):
    """
    通义千问客户端（阿里云百炼）
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        try:
            from openai import OpenAI
            
            api_key = config.get("api_key") or os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("Qwen API key not found. Please set DASHSCOPE_API_KEY environment variable.")
            
            base_url = config.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )
            
            logger.info("Qwen client initialized successfully")
            
        except ImportError:
            raise ImportError("OpenAI library is required for Qwen client. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize Qwen client: {e}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        使用通义千问生成文本
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                timeout=self.timeout
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Qwen API call failed: {e}")
            raise


class OpenAIClient(BaseLLMClient):
    """
    OpenAI客户端
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        try:
            from openai import OpenAI
            
            api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
            
            self.client = OpenAI(
                api_key=api_key,
                base_url=config.get("base_url"),  # 支持自定义base_url
                timeout=self.timeout
            )
            
            logger.info("OpenAI client initialized successfully")
            
        except ImportError:
            raise ImportError("OpenAI library is required. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        使用OpenAI生成文本
        """
        try:
            response = self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise


class ClaudeClient(BaseLLMClient):
    """
    Claude客户端
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        try:
            import anthropic
            
            api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Claude API key not found. Please set ANTHROPIC_API_KEY environment variable.")
            
            self.client = anthropic.Anthropic(
                api_key=api_key,
                timeout=self.timeout
            )
            
            logger.info("Claude client initialized successfully")
            
        except ImportError:
            raise ImportError("Anthropic library is required. Install with: pip install anthropic")
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        使用Claude生成文本
        """
        try:
            response = self.client.messages.create(
                model=kwargs.get("model", self.model),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise


class CustomClient(BaseLLMClient):
    """
    自定义客户端包装器
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self.custom_client = config.get("client")
        if not self.custom_client:
            raise ValueError("Custom client not provided in config")
        
        logger.info("Custom client initialized")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        使用自定义客户端生成文本
        """
        try:
            # 尝试不同的调用方式
            if hasattr(self.custom_client, 'generate'):
                return self.custom_client.generate(prompt, **kwargs)
            elif hasattr(self.custom_client, 'chat'):
                # OpenAI兼容接口
                response = self.custom_client.chat.completions.create(
                    model=kwargs.get("model", self.model),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=kwargs.get("temperature", self.temperature),
                    max_tokens=kwargs.get("max_tokens", self.max_tokens)
                )
                return response.choices[0].message.content
            else:
                # 直接调用
                return self.custom_client(prompt)
                
        except Exception as e:
            logger.error(f"Custom client call failed: {e}")
            raise


def create_llm_client(config: Dict[str, Any]) -> Optional[BaseLLMClient]:
    """
    创建LLM客户端
    
    Args:
        config: LLM配置
        
    Returns:
        LLM客户端实例，如果创建失败则返回None
    """
    if not config.get("enabled", False):
        logger.info("LLM is disabled in configuration")
        return None
    
    provider = config.get("provider", "qwen").lower()
    
    try:
        if provider == "qwen":
            return QwenClient(config)
        elif provider == "openai":
            return OpenAIClient(config)
        elif provider == "claude":
            return ClaudeClient(config)
        elif provider == "custom":
            return CustomClient(config)
        else:
            logger.error(f"Unsupported LLM provider: {provider}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create LLM client for provider {provider}: {e}")
        return None
