#!/usr/bin/env python3
"""
测试继承关系和方法可用性
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter import DocxSplitter


def test_inheritance():
    """测试继承关系"""
    print("🔍 测试继承关系和方法可用性")
    print("=" * 80)
    
    # 创建DocxSplitter实例
    splitter = DocxSplitter(strict_max_tokens=True)
    
    print(f"DocxSplitter类: {type(splitter)}")
    print(f"父类: {type(splitter).__bases__}")
    
    # 检查方法是否存在
    methods_to_check = [
        '_apply_strict_max_tokens',
        '_split_oversized_chunk',
        '_count_tokens',
        'flatten'
    ]
    
    print("\n方法可用性检查:")
    for method_name in methods_to_check:
        has_method = hasattr(splitter, method_name)
        print(f"  {method_name}: {'✅ 存在' if has_method else '❌ 不存在'}")
        
        if has_method:
            method = getattr(splitter, method_name)
            print(f"    类型: {type(method)}")
    
    # 检查属性
    attributes_to_check = [
        'strict_max_tokens',
        'max_tokens',
        'overlap'
    ]
    
    print("\n属性检查:")
    for attr_name in attributes_to_check:
        has_attr = hasattr(splitter, attr_name)
        if has_attr:
            value = getattr(splitter, attr_name)
            print(f"  {attr_name}: {value}")
        else:
            print(f"  {attr_name}: ❌ 不存在")


def test_method_call():
    """测试方法调用"""
    print("\n🧪 测试方法调用")
    print("=" * 80)
    
    splitter = DocxSplitter(
        max_tokens=100,
        strict_max_tokens=True
    )
    
    # 测试_count_tokens方法
    test_text = "这是一个测试文本"
    try:
        token_count = splitter._count_tokens(test_text)
        print(f"✅ _count_tokens工作正常: {token_count}")
    except Exception as e:
        print(f"❌ _count_tokens失败: {e}")
    
    # 测试_apply_strict_max_tokens方法
    long_text = "这是一个很长的文本。" * 20
    try:
        result = splitter._apply_strict_max_tokens([long_text])
        print(f"✅ _apply_strict_max_tokens工作正常: {len(result)} chunks")
        for i, chunk in enumerate(result):
            print(f"  Chunk {i+1}: {len(chunk)} 字符")
    except Exception as e:
        print(f"❌ _apply_strict_max_tokens失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_inheritance()
    test_method_call()
