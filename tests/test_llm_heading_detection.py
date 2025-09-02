#!/usr/bin/env python3
"""
测试LLM标题检测功能
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter import DocxSplitter
from contract_splitter.llm_heading_detector import LLMHeadingDetector


def test_llm_heading_detector_standalone():
    """测试独立的LLM标题检测器"""
    print("🧠 测试独立LLM标题检测器")
    print("=" * 80)
    
    # 创建检测器（不使用真实LLM，只测试规则回退）
    detector = LLMHeadingDetector(llm_client=None)
    
    # 测试文本
    test_texts = [
        "一、项目名称：首创证券新增代销机构 - 广州农商行",
        "（一）公司治理结构完善，内部控制有效 ;",
        "（二）满足监管要求，未见监管部门（证监会、国家金融监督管理总局）针对该机构基金销售业务的停业整改处罚，确保该业务在监管允许范围内正常展业；",
        "1、代销机构依法注册，并且持续经营；",
        "2、代销机构股权结构清晰，实际控制人信用情况良好；",
        "四、代销机构介绍—— 广州农村商业银行股份有限公司",
        "这是一段普通的内容文本，不应该被识别为标题。它包含了完整的句子结构和标点符号。",
        "（三）组织架构完整，设有专门的产品销售业务团队和分管销售业务的高管，销售业务团队的设置能保证业务运营的完整与独立，销售业务团队有满足营业需要的固定场所和安全防范措施 ;"
    ]
    
    # 批量检测
    results = detector.detect_headings_batch(test_texts)
    
    print("检测结果：")
    for i, (text, result) in enumerate(zip(test_texts, results)):
        status = "✅ 标题" if result['is_heading'] else "❌ 内容"
        level = f"(级别{result['level']})" if result['is_heading'] else ""
        confidence = f"置信度{result['confidence']:.2f}"
        print(f"{i+1}. {status} {level} {confidence}")
        print(f"   文本: {text[:60]}...")
        print()


def test_docx_splitter_with_llm():
    """测试集成LLM的DocxSplitter"""
    print("🚀 测试集成LLM的DocxSplitter")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 测试不使用LLM（当前默认行为）
    print("📋 不使用LLM的结果：")
    splitter_no_llm = DocxSplitter(use_llm_heading_detection=False)
    sections_no_llm = splitter_no_llm.split(test_file)
    chunks_no_llm = splitter_no_llm.flatten(sections_no_llm)
    print(f"  Sections: {len(sections_no_llm)}")
    print(f"  Chunks: {len(chunks_no_llm)}")
    
    # 测试使用LLM（但没有真实LLM客户端，会回退到规则检测）
    print("\n📋 启用LLM检测的结果（回退到规则检测）：")
    try:
        splitter_with_llm = DocxSplitter(
            use_llm_heading_detection=True,
            llm_config={
                'llm_type': 'custom',
                'client': None  # 没有真实客户端，会回退
            }
        )
        sections_with_llm = splitter_with_llm.split(test_file)
        chunks_with_llm = splitter_with_llm.flatten(sections_with_llm)
        print(f"  Sections: {len(sections_with_llm)}")
        print(f"  Chunks: {len(chunks_with_llm)}")
        
        # 比较结果
        if len(chunks_no_llm) == len(chunks_with_llm):
            print("  ✅ 结果一致（符合预期，因为回退到规则检测）")
        else:
            print("  ⚠️  结果不一致")
            
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")


def test_mock_llm_client():
    """测试模拟LLM客户端"""
    print("🤖 测试模拟LLM客户端")
    print("=" * 80)
    
    class MockLLMClient:
        """模拟LLM客户端"""
        
        def generate(self, prompt: str) -> str:
            """模拟生成响应"""
            # 简单的模拟逻辑：根据提示中的文本数量返回结果
            import re
            
            # 提取文本数量
            lines = prompt.split('\n')
            text_lines = [line for line in lines if re.match(r'^\d+\.', line.strip())]
            count = len(text_lines)
            
            # 生成模拟响应
            results = []
            for i in range(count):
                # 简单规则：包含"一、"、"二、"等的是1级标题
                if i < len(text_lines):
                    text = text_lines[i]
                    if any(marker in text for marker in ['一、', '二、', '三、', '四、']):
                        results.append({"is_heading": True, "level": 1, "confidence": 0.9})
                    elif any(marker in text for marker in ['（一）', '（二）', '（三）']):
                        # 模拟LLM更智能的判断：长文本不是标题
                        if len(text) > 100:
                            results.append({"is_heading": False, "level": 0, "confidence": 0.8})
                        else:
                            results.append({"is_heading": True, "level": 2, "confidence": 0.7})
                    else:
                        results.append({"is_heading": False, "level": 0, "confidence": 0.6})
                else:
                    results.append({"is_heading": False, "level": 0, "confidence": 0.5})
            
            import json
            return json.dumps(results)
    
    # 创建带模拟LLM的检测器
    mock_client = MockLLMClient()
    detector = LLMHeadingDetector(llm_client=mock_client)
    
    # 测试文本
    test_texts = [
        "一、项目名称：首创证券新增代销机构 - 广州农商行",
        "（一）公司治理结构完善，内部控制有效 ;",
        "（二）满足监管要求，未见监管部门（证监会、国家金融监督管理总局）针对该机构基金销售业务的停业整改处罚，确保该业务在监管允许范围内正常展业；",
        "这是普通内容"
    ]
    
    # 批量检测
    results = detector.detect_headings_batch(test_texts)
    
    print("模拟LLM检测结果：")
    for i, (text, result) in enumerate(zip(test_texts, results)):
        status = "✅ 标题" if result['is_heading'] else "❌ 内容"
        level = f"(级别{result['level']})" if result['is_heading'] else ""
        confidence = f"置信度{result['confidence']:.2f}"
        print(f"{i+1}. {status} {level} {confidence}")
        print(f"   文本: {text[:60]}...")
        print()


def main():
    """主函数"""
    print("🧠 LLM标题检测功能测试")
    print("=" * 80)
    
    test_llm_heading_detector_standalone()
    print("\n" + "=" * 80)
    
    test_docx_splitter_with_llm()
    print("\n" + "=" * 80)
    
    test_mock_llm_client()
    
    print("\n" + "=" * 80)
    print("💡 使用说明：")
    print("1. LLM标题检测是可选功能，默认关闭")
    print("2. 启用时需要提供LLM客户端配置")
    print("3. 如果LLM不可用，会自动回退到规则检测")
    print("4. LLM检测采用批量处理，提高效率")
    print("5. 考虑token限制，智能分批处理")
    
    print("\n🔧 配置示例：")
    print("""
# 使用OpenAI
splitter = DocxSplitter(
    use_llm_heading_detection=True,
    llm_config={
        'llm_type': 'openai',
        'api_key': 'your-api-key'
    }
)

# 使用Claude
splitter = DocxSplitter(
    use_llm_heading_detection=True,
    llm_config={
        'llm_type': 'claude',
        'api_key': 'your-api-key'
    }
)

# 使用自定义客户端
splitter = DocxSplitter(
    use_llm_heading_detection=True,
    llm_config={
        'llm_type': 'custom',
        'client': your_llm_client
    }
)
""")


if __name__ == "__main__":
    main()
