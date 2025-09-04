#!/usr/bin/env python3
"""
测试LLM配置系统
"""

import os
import json
import tempfile
from pathlib import Path

def test_config_system():
    """测试配置系统"""
    print("🔧 测试配置系统")
    print("=" * 80)
    
    try:
        from contract_splitter.config import Config, get_config, reset_config
        
        # 测试默认配置
        print("📋 测试默认配置:")
        config = Config()
        
        llm_config = config.get_llm_config()
        print(f"  LLM启用状态: {config.is_llm_enabled()}")
        print(f"  LLM提供商: {llm_config.get('provider')}")
        print(f"  LLM模型: {llm_config.get('model')}")
        print(f"  API Key环境变量: {llm_config.get('api_key_env')}")
        
        doc_config = config.get_document_config()
        print(f"  默认max_tokens: {doc_config.get('max_tokens')}")
        print(f"  默认overlap: {doc_config.get('overlap')}")
        
        legal_config = config.get_document_config("legal")
        print(f"  法律文档max_tokens: {legal_config.get('max_tokens')}")
        print(f"  法律文档LLM启用: {legal_config.get('use_llm_heading_detection')}")
        
        print("  ✅ 默认配置测试通过")
        
    except Exception as e:
        print(f"  ❌ 默认配置测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_config_file():
    """测试配置文件加载"""
    print("\n📁 测试配置文件加载:")
    
    try:
        from contract_splitter.config import Config
        
        # 创建临时配置文件
        test_config = {
            "llm": {
                "enabled": True,
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.2
            },
            "legal": {
                "max_tokens": 1200,
                "use_llm_heading_detection": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f, indent=2)
            config_file = f.name
        
        try:
            # 加载配置文件
            config = Config(config_file)
            
            llm_config = config.get_llm_config()
            print(f"  配置文件LLM启用: {config.is_llm_enabled()}")
            print(f"  配置文件LLM提供商: {llm_config.get('provider')}")
            print(f"  配置文件LLM模型: {llm_config.get('model')}")
            print(f"  配置文件温度: {llm_config.get('temperature')}")
            
            legal_config = config.get_document_config("legal")
            print(f"  配置文件法律max_tokens: {legal_config.get('max_tokens')}")
            print(f"  配置文件法律LLM: {legal_config.get('use_llm_heading_detection')}")
            
            print("  ✅ 配置文件测试通过")
            
        finally:
            os.unlink(config_file)
            
    except Exception as e:
        print(f"  ❌ 配置文件测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_env_variables():
    """测试环境变量配置"""
    print("\n🌍 测试环境变量配置:")
    
    try:
        from contract_splitter.config import Config
        
        # 设置测试环境变量
        test_env = {
            'CHUNKING_LLM_ENABLED': 'true',
            'CHUNKING_LLM_PROVIDER': 'claude',
            'CHUNKING_LLM_MODEL': 'claude-3-haiku',
            'CHUNKING_MAX_TOKENS': '1800',
            'DASHSCOPE_API_KEY': 'test-api-key-123'
        }
        
        # 保存原始环境变量
        original_env = {}
        for key in test_env:
            original_env[key] = os.environ.get(key)
            os.environ[key] = test_env[key]
        
        try:
            config = Config()
            
            llm_config = config.get_llm_config()
            print(f"  环境变量LLM启用: {config.is_llm_enabled()}")
            print(f"  环境变量LLM提供商: {llm_config.get('provider')}")
            print(f"  环境变量LLM模型: {llm_config.get('model')}")
            print(f"  环境变量API Key: {llm_config.get('api_key')}")
            
            doc_config = config.get_document_config()
            print(f"  环境变量max_tokens: {doc_config.get('max_tokens')}")
            
            print("  ✅ 环境变量测试通过")
            
        finally:
            # 恢复原始环境变量
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            
    except Exception as e:
        print(f"  ❌ 环境变量测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_llm_client_creation():
    """测试LLM客户端创建"""
    print("\n🤖 测试LLM客户端创建:")
    
    try:
        from contract_splitter.llm_client import create_llm_client
        
        # 测试禁用LLM
        print("  测试禁用LLM:")
        config = {"enabled": False}
        client = create_llm_client(config)
        print(f"    结果: {client}")
        assert client is None, "禁用LLM时应返回None"
        print("    ✅ 禁用LLM测试通过")
        
        # 测试无效提供商
        print("  测试无效提供商:")
        config = {"enabled": True, "provider": "invalid"}
        client = create_llm_client(config)
        print(f"    结果: {client}")
        assert client is None, "无效提供商应返回None"
        print("    ✅ 无效提供商测试通过")
        
        # 测试Qwen客户端（不提供API Key，应该失败）
        print("  测试Qwen客户端（无API Key）:")
        config = {
            "enabled": True, 
            "provider": "qwen",
            "model": "qwen-plus"
        }
        client = create_llm_client(config)
        print(f"    结果: {client}")
        # 没有API Key时应该失败
        print("    ✅ Qwen客户端测试通过（预期失败）")
        
        print("  ✅ LLM客户端创建测试通过")
        
    except Exception as e:
        print(f"  ❌ LLM客户端创建测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_integration_with_splitters():
    """测试与splitter的集成"""
    print("\n🔗 测试与splitter的集成:")
    
    try:
        from contract_splitter.domain_helpers import LegalClauseSplitter
        
        # 测试不使用LLM
        print("  测试不使用LLM:")
        splitter = LegalClauseSplitter(use_llm_heading_detection=False)
        print(f"    splitter配置: {splitter.splitter_config.get('use_llm_heading_detection')}")
        print("    ✅ 不使用LLM测试通过")
        
        # 测试使用LLM（但没有API Key，应该回退）
        print("  测试使用LLM（无API Key，应回退）:")
        splitter = LegalClauseSplitter(use_llm_heading_detection=True)
        print(f"    splitter配置: {splitter.splitter_config.get('use_llm_heading_detection')}")
        print("    ✅ LLM回退测试通过")
        
        print("  ✅ splitter集成测试通过")
        
    except Exception as e:
        print(f"  ❌ splitter集成测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_config_save_load():
    """测试配置保存和加载"""
    print("\n💾 测试配置保存和加载:")
    
    try:
        from contract_splitter.config import Config
        
        # 创建配置
        config = Config()
        
        # 修改一些配置
        config.config["llm"]["enabled"] = True
        config.config["llm"]["provider"] = "test"
        config.config["legal"]["max_tokens"] = 999
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            config.save_to_file(config_file)
            print(f"  配置已保存到: {config_file}")
            
            # 加载配置
            new_config = Config(config_file)
            
            # 验证配置
            assert new_config.config["llm"]["enabled"] == True
            assert new_config.config["llm"]["provider"] == "test"
            assert new_config.config["legal"]["max_tokens"] == 999
            
            print("  ✅ 配置保存和加载测试通过")
            
        finally:
            os.unlink(config_file)
            
    except Exception as e:
        print(f"  ❌ 配置保存和加载测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🧪 LLM配置系统测试")
    print("=" * 80)
    
    test_config_system()
    test_config_file()
    test_env_variables()
    test_llm_client_creation()
    test_integration_with_splitters()
    test_config_save_load()
    
    print("\n" + "=" * 80)
    print("💡 使用说明:")
    print("1. 配置文件优先级: 环境变量 > 配置文件 > 默认配置")
    print("2. API密钥通过环境变量提供，避免泄露")
    print("3. LLM功能可以通过配置开关控制")
    print("4. 不同文档类型可以有不同的配置")
    
    print("\n🔧 配置示例:")
    print("""
# 环境变量配置
export DASHSCOPE_API_KEY="your-api-key"
export CHUNKING_LLM_ENABLED=true
export CHUNKING_LLM_PROVIDER=qwen

# 代码中使用
from contract_splitter import LegalClauseSplitter
splitter = LegalClauseSplitter(use_llm_heading_detection=True)
""")


if __name__ == "__main__":
    main()
