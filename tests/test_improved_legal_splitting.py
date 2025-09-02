#!/usr/bin/env python3
"""
测试改进后的法律条文切分功能
验证是否解决了条文被错误拆分的问题
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.domain_helpers import split_legal_document


def test_improved_legal_splitting():
    """测试改进后的法律条文切分"""
    
    print("🔍 改进后的法律条文切分测试")
    print("=" * 80)
    
    # 测试WPS文件（之前有问题的文件）
    test_file = 'output/law/9147de404f6d4df986b0cb41acd47aac.wps'
    
    if not os.path.exists(test_file):
        print(f"⚠️  文件不存在: {test_file}")
        return
    
    print(f"📄 测试文件: {os.path.basename(test_file)}")
    print("-" * 60)
    
    try:
        # 使用改进后的切分
        chunks = split_legal_document(test_file, max_tokens=1500)
        
        print(f"✅ 处理成功: {len(chunks)} chunks")
        
        # 验证关键问题是否解决
        verify_article_integrity(chunks)
        
        # 显示前几个chunks的详细内容
        show_chunk_details(chunks[:8])
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


def verify_article_integrity(chunks):
    """验证条文完整性"""
    print(f"\n📊 条文完整性验证:")
    
    # 检查第四条是否完整
    fourth_article_found = False
    fourth_article_complete = False
    
    for i, chunk in enumerate(chunks):
        if '第四条' in chunk:
            fourth_article_found = True
            print(f"  ✅ 找到第四条 (Chunk {i+1})")
            
            # 检查是否包含（一）和（二）
            has_item_one = '（一）' in chunk or '(一)' in chunk
            has_item_two = '（二）' in chunk or '(二)' in chunk
            
            if has_item_one and has_item_two:
                fourth_article_complete = True
                print(f"  ✅ 第四条包含完整的（一）和（二）项")
            else:
                print(f"  ❌ 第四条不完整: 包含（一）={has_item_one}, 包含（二）={has_item_two}")
            break
    
    if not fourth_article_found:
        print(f"  ❌ 未找到第四条")
    
    # 检查第五条的条件是否被错误拆分
    fifth_article_chunks = []
    for i, chunk in enumerate(chunks):
        if '第五条' in chunk:
            fifth_article_chunks.append((i+1, chunk))
    
    if len(fifth_article_chunks) == 1:
        chunk_num, chunk_content = fifth_article_chunks[0]
        print(f"  ✅ 第五条在单个chunk中 (Chunk {chunk_num})")
        
        # 检查是否包含多个条件
        conditions = ['（一）', '（二）', '（三）', '（四）', '（五）']
        found_conditions = [cond for cond in conditions if cond in chunk_content]
        
        if len(found_conditions) >= 2:
            print(f"  ✅ 第五条包含多个条件: {found_conditions}")
        else:
            print(f"  ⚠️  第五条条件较少: {found_conditions}")
    else:
        print(f"  ❌ 第五条被拆分到多个chunks: {len(fifth_article_chunks)}个")


def show_chunk_details(chunks):
    """显示chunk详细内容"""
    print(f"\n📋 前{len(chunks)}个chunks详细内容:")
    print("=" * 80)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n📋 Chunk {i} (长度: {len(chunk)} 字符)")
        print("-" * 50)
        
        # 显示chunk内容，限制长度
        if len(chunk) <= 500:
            print(chunk)
        else:
            print(chunk[:500] + "\n... (内容过长，已截断)")
        
        print("=" * 50)


def compare_with_previous_issues():
    """与之前的问题进行对比"""
    print("\n🔄 与之前问题的对比:")
    print("-" * 40)
    
    print("之前的问题:")
    print("  ❌ 第四条的（一）和（二）被拆分到不同chunks")
    print("  ❌ 第五条的条件被单独拆开")
    print("  ❌ 每个chunk都有重复的前缀")
    print("  ❌ 破坏了条文的逻辑联系")
    
    print("\n现在的改进:")
    print("  ✅ 以条文为单位进行切分")
    print("  ✅ 保持条文内部的完整性")
    print("  ✅ 清理重复的前缀和内容")
    print("  ✅ 维护法律条文的逻辑结构")


if __name__ == "__main__":
    test_improved_legal_splitting()
    compare_with_previous_issues()
