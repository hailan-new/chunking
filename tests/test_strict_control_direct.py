#!/usr/bin/env python3
"""
直接测试严格chunk控制功能
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter import DocxSplitter


def test_direct_strict_control():
    """直接测试严格控制功能"""
    print("🔧 直接测试严格chunk控制功能")
    print("=" * 80)
    
    # 创建一个超长的chunk
    long_chunk = """这是一个超长的文本块。""" * 100  # 重复100次
    
    print(f"原始chunk长度: {len(long_chunk)} 字符")
    
    # 创建splitter
    splitter = DocxSplitter(
        max_tokens=200,  # 设置很小的限制
        overlap=50,
        strict_max_tokens=True
    )
    
    # 直接测试_apply_strict_max_tokens方法
    print("\n直接调用_apply_strict_max_tokens方法:")
    result_chunks = splitter._apply_strict_max_tokens([long_chunk])
    
    print(f"分割后chunks数量: {len(result_chunks)}")
    for i, chunk in enumerate(result_chunks):
        print(f"  Chunk {i+1}: {len(chunk)} 字符")
        if len(chunk) > 200:
            print(f"    ⚠️ 仍然超过限制!")
        else:
            print(f"    ✅ 在限制内")
    
    # 显示前几个chunk的内容
    print(f"\n前3个chunk的内容:")
    for i, chunk in enumerate(result_chunks[:3]):
        print(f"Chunk {i+1}: {chunk[:50]}...")


def test_sentence_splitting_direct():
    """直接测试句子分割功能"""
    print("\n✂️ 直接测试句子分割功能")
    print("=" * 80)
    
    # 创建包含多个句子的长文本
    long_text = """
第一个句子包含一些内容。第二个句子也包含内容！第三个句子包含更多内容？第四个句子继续；第五个句子结束。
这是另一个很长的句子，它包含了大量的文字内容，目的是测试当单个句子超过限制时系统的处理能力和分割策略。
第六个句子比较短。第七个句子也很短。第八个句子稍微长一些但仍然在合理范围内。
"""
    
    print(f"原始文本长度: {len(long_text)} 字符")
    
    splitter = DocxSplitter(
        max_tokens=100,  # 很小的限制
        overlap=20,
        strict_max_tokens=True
    )
    
    # 直接测试_split_oversized_chunk方法
    print("\n直接调用_split_oversized_chunk方法:")
    result_chunks = splitter._split_oversized_chunk(long_text)
    
    print(f"分割后chunks数量: {len(result_chunks)}")
    for i, chunk in enumerate(result_chunks):
        print(f"  Chunk {i+1}: {len(chunk)} 字符")
        print(f"    内容: {chunk.strip()[:80]}...")
        print()


def test_overlap_direct():
    """直接测试overlap功能"""
    print("🔄 直接测试overlap功能")
    print("=" * 80)
    
    test_text = "这是第一句。这是第二句。这是第三句。这是第四句。这是第五句。这是第六句。"
    
    splitter = DocxSplitter(
        max_tokens=30,  # 很小的限制
        overlap=10,
        strict_max_tokens=True
    )
    
    # 直接测试overlap功能
    result_chunks = splitter._split_oversized_chunk(test_text)
    
    print(f"原始文本: {test_text}")
    print(f"分割后chunks数量: {len(result_chunks)}")
    
    for i, chunk in enumerate(result_chunks):
        print(f"Chunk {i+1}: {chunk}")
    
    # 检查overlap
    print("\n检查overlap:")
    for i in range(len(result_chunks) - 1):
        current = result_chunks[i]
        next_chunk = result_chunks[i + 1]
        
        # 简单检查是否有重叠内容
        current_words = current.split()[-3:]  # 取最后3个词
        next_words = next_chunk.split()[:5]   # 取前5个词
        
        overlap_found = any(word in next_words for word in current_words if len(word) > 1)
        print(f"  Chunk {i+1} -> Chunk {i+2}: {'✅ 有overlap' if overlap_found else '❌ 无overlap'}")


def main():
    """主函数"""
    print("🧪 严格chunk控制功能直接测试")
    print("=" * 80)
    
    test_direct_strict_control()
    test_sentence_splitting_direct()
    test_overlap_direct()
    
    print("\n" + "=" * 80)
    print("🎯 直接测试完成")


if __name__ == "__main__":
    main()
