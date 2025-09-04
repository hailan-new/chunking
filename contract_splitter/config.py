"""
配置管理模块
支持LLM配置、环境变量和默认设置的统一管理
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Config:
    """
    统一配置管理类
    支持LLM配置、环境变量和默认设置
    """
    
    # 默认配置
    DEFAULT_CONFIG = {
        # LLM配置
        "llm": {
            "enabled": False,
            "provider": "qwen",  # qwen, openai, claude, custom
            "model": "qwen-plus",
            "api_key_env": "DASHSCOPE_API_KEY",  # 环境变量名
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "temperature": 0.1,
            "max_tokens": 1000,
            "timeout": 30,
            "retry_times": 3,
            "batch_size": 20,
            "max_tokens_per_batch": 3000,
            "cache_enabled": True
        },
        
        # 文档处理配置
        "document": {
            "max_tokens": 2000,
            "overlap": 200,
            "split_by_sentence": True,
            "token_counter": "character",
            "chunking_strategy": "finest_granularity",
            "strict_max_tokens": False
        },
        
        # 法律文档特殊配置
        "legal": {
            "max_tokens": 1500,
            "overlap": 100,
            "strict_max_tokens": True,
            "use_llm_heading_detection": False
        },
        
        # 合同文档配置
        "contract": {
            "max_tokens": 2000,
            "overlap": 200,
            "strict_max_tokens": True,
            "use_llm_heading_detection": False
        },
        
        # 规章制度配置
        "regulation": {
            "max_tokens": 1800,
            "overlap": 150,
            "strict_max_tokens": True,
            "use_llm_heading_detection": True  # 规章制度建议使用LLM
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认配置
        """
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = config_file
        
        # 加载配置文件
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        
        # 从环境变量更新配置
        self.load_from_env()
    
    def load_from_file(self, config_file: str):
        """
        从配置文件加载配置
        
        Args:
            config_file: 配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # 深度合并配置
            self._deep_merge(self.config, file_config)
            logger.info(f"Loaded configuration from {config_file}")
            
        except Exception as e:
            logger.warning(f"Failed to load config file {config_file}: {e}")
    
    def load_from_env(self):
        """
        从环境变量加载配置
        """
        # LLM相关环境变量
        env_mappings = {
            "CHUNKING_LLM_ENABLED": ("llm", "enabled", bool),
            "CHUNKING_LLM_PROVIDER": ("llm", "provider", str),
            "CHUNKING_LLM_MODEL": ("llm", "model", str),
            "CHUNKING_LLM_BASE_URL": ("llm", "base_url", str),
            "CHUNKING_LLM_TEMPERATURE": ("llm", "temperature", float),
            "CHUNKING_LLM_MAX_TOKENS": ("llm", "max_tokens", int),
            "CHUNKING_LLM_TIMEOUT": ("llm", "timeout", int),
            "CHUNKING_LLM_RETRY_TIMES": ("llm", "retry_times", int),
            "CHUNKING_LLM_BATCH_SIZE": ("llm", "batch_size", int),
            "CHUNKING_LLM_CACHE_ENABLED": ("llm", "cache_enabled", bool),
            
            # 文档处理相关环境变量
            "CHUNKING_MAX_TOKENS": ("document", "max_tokens", int),
            "CHUNKING_OVERLAP": ("document", "overlap", int),
            "CHUNKING_STRICT_MAX_TOKENS": ("document", "strict_max_tokens", bool),
        }
        
        for env_var, (section, key, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    if value_type == bool:
                        parsed_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == int:
                        parsed_value = int(env_value)
                    elif value_type == float:
                        parsed_value = float(env_value)
                    else:
                        parsed_value = env_value
                    
                    self.config[section][key] = parsed_value
                    logger.debug(f"Updated config from env: {section}.{key} = {parsed_value}")
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid value for {env_var}: {env_value}, error: {e}")
    
    def get_llm_config(self) -> Dict[str, Any]:
        """
        获取LLM配置
        
        Returns:
            LLM配置字典
        """
        llm_config = self.config["llm"].copy()
        
        # 从环境变量获取API Key
        api_key_env = llm_config.get("api_key_env")
        if api_key_env:
            api_key = os.getenv(api_key_env)
            if api_key:
                llm_config["api_key"] = api_key
            else:
                logger.warning(f"API key not found in environment variable: {api_key_env}")
        
        return llm_config
    
    def get_document_config(self, document_type: str = "document") -> Dict[str, Any]:
        """
        获取文档处理配置
        
        Args:
            document_type: 文档类型 (document, legal, contract, regulation)
            
        Returns:
            文档处理配置字典
        """
        base_config = self.config["document"].copy()
        
        # 如果有特定类型的配置，则合并
        if document_type in self.config:
            type_config = self.config[document_type].copy()
            base_config.update(type_config)
        
        return base_config
    
    def is_llm_enabled(self) -> bool:
        """
        检查LLM是否启用
        
        Returns:
            True if LLM is enabled
        """
        return self.config["llm"]["enabled"]
    
    def save_to_file(self, config_file: str):
        """
        保存配置到文件
        
        Args:
            config_file: 配置文件路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save config to {config_file}: {e}")
    
    def _deep_merge(self, base_dict: Dict, update_dict: Dict):
        """
        深度合并字典
        
        Args:
            base_dict: 基础字典
            update_dict: 更新字典
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value


# 全局配置实例
_global_config = None


def get_config(config_file: Optional[str] = None) -> Config:
    """
    获取全局配置实例
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置实例
    """
    global _global_config
    
    if _global_config is None:
        _global_config = Config(config_file)
    
    return _global_config


def reset_config():
    """
    重置全局配置实例
    """
    global _global_config
    _global_config = None
