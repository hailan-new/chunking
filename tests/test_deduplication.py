#!/usr/bin/env python3
"""
测试去重功能
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter import ContractSplitter


def advanced_deduplication(chunks):
    """
    高级去重功能：检测并移除重复和高度相似的chunks
    
    Args:
        chunks: 原始chunks列表
        
    Returns:
        去重后的chunks列表
    """
    if not chunks:
        return chunks
    
    unique_chunks = []
    seen_fingerprints = set()
    
    for i, chunk in enumerate(chunks):
        # 创建内容指纹
        fingerprint = create_content_fingerprint(chunk)
        
        # 检查是否与已有chunks重复
        is_duplicate = False
        for seen_fp in seen_fingerprints:
            if chunks_are_similar(fingerprint, seen_fp, threshold=0.7):
                print(f"🔍 发现重复chunk {i+1}: 与之前的chunk相似度过高")
                is_duplicate = True
                break
        
        if not is_duplicate:
            seen_fingerprints.add(fingerprint)
            unique_chunks.append(chunk)
        
    return unique_chunks


def create_content_fingerprint(text):
    """
    创建内容指纹，用于相似性检测
    
    Args:
        text: 文本内容
        
    Returns:
        内容指纹字符串
    """
    # 移除格式标记和空白字符
    import re
    
    # 移除chunk标题和分隔符
    clean_text = re.sub(r'【Chunk \d+】.*?\n', '', text)
    clean_text = re.sub(r'={50,}', '', clean_text)
    clean_text = re.sub(r'-{20,}', '', clean_text)
    clean_text = re.sub(r'\(长度: \d+ 字符\)', '', clean_text)
    
    # 移除多余空白
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    # 取前500字符作为指纹
    return clean_text[:500]


def chunks_are_similar(text1, text2, threshold=0.7):
    """
    检查两个文本是否相似
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
        threshold: 相似度阈值
        
    Returns:
        True if similar
    """
    if not text1 or not text2:
        return False
    
    # 计算字符级别的相似度
    set1 = set(text1.lower())
    set2 = set(text2.lower())
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return False
    
    similarity = intersection / union
    return similarity >= threshold


def test_deduplication():
    """测试去重功能"""
    print("🔍 测试去重功能")
    print("=" * 60)
    
    # 测试文件
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    try:
        # 创建分割器
        splitter = ContractSplitter(
            max_tokens=1000,
            overlap=100,
            split_by_sentence=True,
            token_counter="character"
        )
        
        # 分割文档
        print(f"📄 处理文件: {test_file}")
        sections = splitter.split(test_file)
        original_chunks = splitter.flatten(sections)
        
        print(f"📊 原始chunks数量: {len(original_chunks)}")
        
        # 应用高级去重
        deduplicated_chunks = advanced_deduplication(original_chunks)
        
        print(f"📊 去重后chunks数量: {len(deduplicated_chunks)}")
        print(f"📊 去除重复chunks: {len(original_chunks) - len(deduplicated_chunks)} 个")
        
        # 检查特定重复内容
        duplicate_patterns = [
            "一、项目名称：首创证券新增代销机构-广州农商行",
            "二、项目背景：",
            "四、代销机构介绍"
        ]
        
        print("\n🔍 检查特定重复模式:")
        for pattern in duplicate_patterns:
            original_count = sum(1 for chunk in original_chunks if pattern in chunk)
            deduplicated_count = sum(1 for chunk in deduplicated_chunks if pattern in chunk)
            
            print(f"  '{pattern[:20]}...': {original_count} -> {deduplicated_count}")
        
        # 保存去重后的结果
        output_file = "output/deduplicated_chunks.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, chunk in enumerate(deduplicated_chunks, 1):
                f.write(f"【Chunk {i:03d}】 (长度: {len(chunk)} 字符)\n")
                f.write("-" * 40 + "\n")
                f.write(chunk + "\n")
                f.write("=" * 80 + "\n\n")
        
        print(f"\n✅ 去重后的结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 去重功能测试")
    print("=" * 80)
    
    success = test_deduplication()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 测试完成！请查看去重效果")
    else:
        print("❌ 测试失败！")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
