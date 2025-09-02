#!/usr/bin/env python3
"""
测试新增的改进功能
1. 文本清理（保留换行）
2. 严格chunk大小控制
3. 专业领域helper函数
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter import DocxSplitter
from contract_splitter.domain_helpers import (
    split_legal_document,
    split_contract,
    split_regulation,
    LegalClauseSplitter,
    DomainContractSplitter,
    RegulationSplitter
)


def test_text_cleaning():
    """测试文本清理功能"""
    print("🧹 测试文本清理功能")
    print("=" * 80)
    
    from contract_splitter.utils import clean_text
    
    test_texts = [
        "这是  一个  有  多余  空格  的  文本",
        "中文 和 English 混合 的 text",
        "保留\n换行\n符号\n的文本",
        "去除  多余  空格\n但是\n保留\n换行",
        "标点  符号  ，  也要  处理  。",
        "（  括号  ）  和  【  方括号  】"
    ]
    
    for i, text in enumerate(test_texts):
        cleaned = clean_text(text)
        print(f"测试 {i+1}:")
        print(f"  原文: {repr(text)}")
        print(f"  清理: {repr(cleaned)}")
        print()


def test_strict_max_tokens():
    """测试严格chunk大小控制"""
    print("📏 测试严格chunk大小控制")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 测试不严格控制（默认）
    print("📋 不严格控制chunk大小:")
    splitter_loose = DocxSplitter(
        max_tokens=1000,  # 设置较小的限制来测试
        strict_max_tokens=False
    )
    
    sections = splitter_loose.split(test_file)
    chunks_loose = splitter_loose.flatten(sections)
    
    print(f"  总chunks: {len(chunks_loose)}")
    oversized_loose = [i for i, chunk in enumerate(chunks_loose)
                      if len(chunk) > 1000]
    print(f"  超过1000字符的chunks: {len(oversized_loose)}")
    if oversized_loose:
        for i in oversized_loose[:3]:  # 显示前3个
            size = len(chunks_loose[i])
            print(f"    Chunk {i+1}: {size} 字符")
    
    # 测试严格控制
    print("\n📋 严格控制chunk大小:")
    splitter_strict = DocxSplitter(
        max_tokens=1000,
        overlap=100,
        strict_max_tokens=True
    )
    
    sections = splitter_strict.split(test_file)
    chunks_strict = splitter_strict.flatten(sections)
    
    print(f"  总chunks: {len(chunks_strict)}")
    oversized_strict = [i for i, chunk in enumerate(chunks_strict)
                       if len(chunk) > 1000]
    print(f"  超过1000字符的chunks: {len(oversized_strict)}")
    if oversized_strict:
        for i in oversized_strict[:3]:  # 显示前3个
            size = len(chunks_strict[i])
            print(f"    Chunk {i+1}: {size} 字符")
    
    # 显示chunk大小分布
    print(f"\n📊 Chunk大小分布:")
    print(f"  不严格控制: 平均{sum(len(c) for c in chunks_loose)/len(chunks_loose):.0f}字符")
    print(f"  严格控制: 平均{sum(len(c) for c in chunks_strict)/len(chunks_strict):.0f}字符")


def test_domain_helpers():
    """测试专业领域helper函数"""
    print("🏛️ 测试专业领域helper函数")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 测试法律条款切分器
    print("⚖️ 法律条款切分器:")
    try:
        legal_chunks = split_legal_document(test_file, max_tokens=1500)
        print(f"  法律文档切分: {len(legal_chunks)} 个chunks")
        print(f"  平均长度: {sum(len(c) for c in legal_chunks)/len(legal_chunks):.0f} 字符")
        print(f"  最大长度: {max(len(c) for c in legal_chunks)} 字符")
    except Exception as e:
        print(f"  ❌ 法律切分失败: {e}")
    
    # 测试合同切分器
    print("\n📄 合同切分器:")
    contract_types = ["general", "service", "purchase"]
    
    for contract_type in contract_types:
        try:
            contract_chunks = split_contract(test_file, contract_type=contract_type)
            print(f"  {contract_type}合同: {len(contract_chunks)} 个chunks")
        except Exception as e:
            print(f"  ❌ {contract_type}合同切分失败: {e}")
    
    # 测试规章制度切分器
    print("\n📋 规章制度切分器:")
    regulation_types = ["general", "hr", "finance"]
    
    for regulation_type in regulation_types:
        try:
            regulation_chunks = split_regulation(test_file, regulation_type=regulation_type)
            print(f"  {regulation_type}规章: {len(regulation_chunks)} 个chunks")
        except Exception as e:
            print(f"  ❌ {regulation_type}规章切分失败: {e}")


def test_domain_splitter_classes():
    """测试专业领域切分器类"""
    print("🔧 测试专业领域切分器类")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 测试法律条款切分器类
    print("⚖️ LegalClauseSplitter:")
    try:
        legal_splitter = LegalClauseSplitter(
            max_tokens=1200,
            strict_max_tokens=True
        )
        legal_chunks = legal_splitter.split_legal_document(test_file)
        print(f"  切分结果: {len(legal_chunks)} 个chunks")
        
        # 检查是否有超过限制的chunks
        oversized = [i for i, chunk in enumerate(legal_chunks)
                    if len(chunk) > 1200]
        print(f"  超过限制的chunks: {len(oversized)}")
        
    except Exception as e:
        print(f"  ❌ 失败: {e}")
    
    # 测试合同切分器类
    print("\n📄 DomainContractSplitter:")
    try:
        contract_splitter = DomainContractSplitter(
            contract_type="service",
            max_tokens=1500,
            strict_max_tokens=True
        )
        contract_chunks = contract_splitter.split_contract(test_file)
        print(f"  服务合同切分: {len(contract_chunks)} 个chunks")
        
    except Exception as e:
        print(f"  ❌ 失败: {e}")
    
    # 测试规章制度切分器类
    print("\n📋 RegulationSplitter:")
    try:
        regulation_splitter = RegulationSplitter(
            regulation_type="finance",
            max_tokens=1800,
            strict_max_tokens=True
        )
        regulation_chunks = regulation_splitter.split_regulation(test_file)
        print(f"  财务规章切分: {len(regulation_chunks)} 个chunks")
        
    except Exception as e:
        print(f"  ❌ 失败: {e}")


def main():
    """主函数"""
    print("🚀 测试新增改进功能")
    print("=" * 80)
    
    test_text_cleaning()
    print("\n" + "=" * 80)
    
    test_strict_max_tokens()
    print("\n" + "=" * 80)
    
    test_domain_helpers()
    print("\n" + "=" * 80)
    
    test_domain_splitter_classes()
    
    print("\n" + "=" * 80)
    print("🎯 测试完成")
    print("\n💡 新功能说明:")
    print("1. 文本清理：去除字间多余空格，保留换行符")
    print("2. 严格chunk控制：可选择严格控制chunk大小，超过限制时自动分割")
    print("3. 专业领域helper：针对法律、合同、规章制度的专门切分器")
    print("4. 智能参数配置：根据文档类型自动调整切分参数")
    print("5. 语义完整性：保持专业文档的语义连贯性")


if __name__ == "__main__":
    main()
