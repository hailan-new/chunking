#!/usr/bin/env python3
"""
LLM配置系统使用示例
演示如何配置和使用LLM功能
"""

import os
import sys
import tempfile
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def example_1_basic_usage():
    """示例1: 基本使用方法"""
    print("📋 示例1: 基本使用方法")
    print("-" * 60)
    
    from contract_splitter import LegalClauseSplitter
    
    # 方法1: 不使用LLM（默认）
    print("1. 不使用LLM（默认）:")
    splitter = LegalClauseSplitter()
    print(f"   LLM启用状态: {splitter.splitter_config.get('use_llm_heading_detection')}")
    
    # 方法2: 启用LLM但没有API Key（会回退到规则检测）
    print("2. 启用LLM但没有API Key:")
    splitter = LegalClauseSplitter(use_llm_heading_detection=True)
    print(f"   LLM启用状态: {splitter.splitter_config.get('use_llm_heading_detection')}")
    
    print("   ✅ 基本使用示例完成\n")


def example_2_env_config():
    """示例2: 环境变量配置"""
    print("📋 示例2: 环境变量配置")
    print("-" * 60)
    
    # 设置环境变量
    os.environ['DASHSCOPE_API_KEY'] = 'sk-test-key-123'
    os.environ['CHUNKING_LLM_ENABLED'] = 'true'
    os.environ['CHUNKING_LLM_PROVIDER'] = 'qwen'
    os.environ['CHUNKING_LLM_MODEL'] = 'qwen-plus'
    
    from contract_splitter.config import get_config, reset_config
    from contract_splitter import LegalClauseSplitter

    # 重置配置以加载新的环境变量
    reset_config()

    # 获取配置
    config = get_config()
    llm_config = config.get_llm_config()
    
    print("环境变量配置:")
    print(f"   LLM启用: {config.is_llm_enabled()}")
    print(f"   LLM提供商: {llm_config.get('provider')}")
    print(f"   LLM模型: {llm_config.get('model')}")
    print(f"   API Key: {llm_config.get('api_key')[:10]}..." if llm_config.get('api_key') else "   API Key: None")
    
    # 使用配置创建splitter
    splitter = LegalClauseSplitter()  # 会自动从配置获取LLM设置
    print(f"   Splitter LLM启用: {splitter.splitter_config.get('use_llm_heading_detection')}")
    
    print("   ✅ 环境变量配置示例完成\n")


def example_3_config_file():
    """示例3: 配置文件使用"""
    print("📋 示例3: 配置文件使用")
    print("-" * 60)
    
    # 创建临时配置文件
    config_data = {
        "llm": {
            "enabled": True,
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "api_key_env": "OPENAI_API_KEY",
            "temperature": 0.2,
            "max_tokens": 800
        },
        "legal": {
            "max_tokens": 1200,
            "overlap": 80,
            "use_llm_heading_detection": True
        },
        "contract": {
            "max_tokens": 2500,
            "use_llm_heading_detection": False
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f, indent=2)
        config_file = f.name
    
    try:
        from contract_splitter.config import Config
        from contract_splitter import LegalClauseSplitter, DomainContractSplitter
        
        # 使用配置文件创建配置
        config = Config(config_file)
        
        print("配置文件内容:")
        llm_config = config.get_llm_config()
        print(f"   LLM启用: {config.is_llm_enabled()}")
        print(f"   LLM提供商: {llm_config.get('provider')}")
        print(f"   LLM模型: {llm_config.get('model')}")
        print(f"   温度: {llm_config.get('temperature')}")
        
        legal_config = config.get_document_config("legal")
        print(f"   法律文档max_tokens: {legal_config.get('max_tokens')}")
        print(f"   法律文档LLM: {legal_config.get('use_llm_heading_detection')}")
        
        contract_config = config.get_document_config("contract")
        print(f"   合同文档max_tokens: {contract_config.get('max_tokens')}")
        print(f"   合同文档LLM: {contract_config.get('use_llm_heading_detection')}")
        
        # 使用配置创建splitter
        legal_splitter = LegalClauseSplitter(config_file=config_file)
        contract_splitter = DomainContractSplitter(config_file=config_file)
        
        print("Splitter配置:")
        print(f"   法律splitter max_tokens: {legal_splitter.splitter_config.get('max_tokens')}")
        print(f"   合同splitter max_tokens: {contract_splitter.splitter_config.get('max_tokens')}")
        
    finally:
        os.unlink(config_file)
    
    print("   ✅ 配置文件示例完成\n")


def example_4_custom_llm_config():
    """示例4: 自定义LLM配置"""
    print("📋 示例4: 自定义LLM配置")
    print("-" * 60)
    
    from contract_splitter import LegalClauseSplitter
    
    # 方法1: 直接传递LLM配置
    llm_config = {
        "enabled": True,
        "provider": "qwen",
        "model": "qwen-turbo",
        "api_key": "sk-custom-key-456",
        "temperature": 0.1,
        "max_tokens": 1200
    }
    
    splitter = LegalClauseSplitter(
        use_llm_heading_detection=True,
        llm_config=llm_config
    )
    
    print("自定义LLM配置:")
    print(f"   LLM启用: {splitter.splitter_config.get('use_llm_heading_detection')}")
    print(f"   LLM配置: {splitter.splitter_config.get('llm_config', {}).get('provider')}")
    
    # 方法2: 使用自定义客户端
    class MockLLMClient:
        def generate(self, prompt):
            return "这是模拟的LLM响应"
    
    custom_llm_config = {
        "enabled": True,
        "provider": "custom",
        "client": MockLLMClient()
    }
    
    splitter2 = LegalClauseSplitter(
        use_llm_heading_detection=True,
        llm_config=custom_llm_config
    )
    
    print("自定义客户端配置:")
    print(f"   LLM启用: {splitter2.splitter_config.get('use_llm_heading_detection')}")
    print(f"   自定义客户端: {type(custom_llm_config['client']).__name__}")
    
    print("   ✅ 自定义LLM配置示例完成\n")


def example_5_priority_demo():
    """示例5: 配置优先级演示"""
    print("📋 示例5: 配置优先级演示")
    print("-" * 60)
    
    # 创建配置文件
    config_data = {
        "llm": {
            "enabled": False,
            "provider": "openai",
            "model": "gpt-4"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f, indent=2)
        config_file = f.name
    
    try:
        # 设置环境变量（优先级更高）
        os.environ['CHUNKING_LLM_ENABLED'] = 'true'
        os.environ['CHUNKING_LLM_PROVIDER'] = 'claude'
        os.environ['CHUNKING_LLM_MODEL'] = 'claude-3-haiku'
        
        from contract_splitter.config import Config
        
        config = Config(config_file)
        llm_config = config.get_llm_config()
        
        print("配置优先级演示:")
        print("配置文件设置: enabled=False, provider=openai, model=gpt-4")
        print("环境变量设置: enabled=true, provider=claude, model=claude-3-haiku")
        print()
        print("最终配置（环境变量优先）:")
        print(f"   LLM启用: {config.is_llm_enabled()}")
        print(f"   LLM提供商: {llm_config.get('provider')}")
        print(f"   LLM模型: {llm_config.get('model')}")
        
    finally:
        os.unlink(config_file)
        # 清理环境变量
        for key in ['CHUNKING_LLM_ENABLED', 'CHUNKING_LLM_PROVIDER', 'CHUNKING_LLM_MODEL']:
            os.environ.pop(key, None)
    
    print("   ✅ 配置优先级演示完成\n")


def main():
    """主函数"""
    print("🚀 LLM配置系统使用示例")
    print("=" * 80)
    
    example_1_basic_usage()
    example_2_env_config()
    example_3_config_file()
    example_4_custom_llm_config()
    example_5_priority_demo()
    
    print("=" * 80)
    print("📚 总结:")
    print("1. 支持多种配置方式：环境变量、配置文件、代码参数")
    print("2. 配置优先级：环境变量 > 配置文件 > 默认配置")
    print("3. API密钥通过环境变量提供，确保安全")
    print("4. 支持多种LLM提供商：Qwen、OpenAI、Claude、自定义")
    print("5. 不同文档类型可以有不同的配置")
    print("6. LLM功能可以随时开启/关闭")
    
    print("\n🔧 快速开始:")
    print("""
# 1. 设置环境变量
export DASHSCOPE_API_KEY="your-api-key"
export CHUNKING_LLM_ENABLED=true

# 2. 使用LLM功能
from contract_splitter import LegalClauseSplitter
splitter = LegalClauseSplitter(use_llm_heading_detection=True)
chunks = splitter.split_legal_document("document.pdf")
""")


if __name__ == "__main__":
    main()
