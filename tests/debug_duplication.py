#!/usr/bin/env python3
"""
诊断重复内容产生的原因
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter import ContractSplitter


def debug_duplication_source():
    """调试重复内容的产生源头"""
    print("🔍 调试重复内容产生源头")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 创建分割器
    splitter = ContractSplitter(
        max_tokens=1000,
        overlap=100,
        split_by_sentence=True,
        token_counter="character"
    )
    
    print("📄 步骤1: 分割文档为sections")
    sections = splitter.split(test_file)
    print(f"   得到 {len(sections)} 个sections")
    
    # 分析每个section的内容
    for i, section in enumerate(sections):
        print(f"\n📋 Section {i+1}:")
        print(f"   标题: {section.get('heading', 'N/A')}")
        print(f"   内容长度: {len(section.get('content', ''))}")
        print(f"   子章节数: {len(section.get('subsections', []))}")
        
        # 检查内容中是否包含重复的关键词
        content = section.get('content', '')
        key_phrases = [
            "一、项目名称：首创证券新增代销机构-广州农商行",
            "二、项目背景：",
            "四、代销机构介绍"
        ]
        
        for phrase in key_phrases:
            count = content.count(phrase)
            if count > 0:
                print(f"   🔍 包含 '{phrase[:30]}...': {count} 次")
        
        # 显示内容的前200字符
        if content:
            preview = content[:200].replace('\n', ' ')
            print(f"   内容预览: {preview}...")
    
    print("\n📄 步骤2: 展平sections为chunks")
    chunks = splitter.flatten(sections)
    print(f"   得到 {len(chunks)} 个chunks")
    
    # 分析chunks中的重复
    print("\n🔍 分析chunks中的重复内容:")
    key_phrases = [
        "一、项目名称：首创证券新增代销机构-广州农商行",
        "二、项目背景：",
        "四、代销机构介绍"
    ]
    
    for phrase in key_phrases:
        matching_chunks = []
        for i, chunk in enumerate(chunks):
            if phrase in chunk:
                matching_chunks.append(i + 1)
        
        if len(matching_chunks) > 1:
            print(f"   ⚠️  '{phrase[:30]}...' 出现在chunks: {matching_chunks}")
    
    # 详细分析重复chunks的内容来源
    print("\n🔍 详细分析重复chunks:")
    target_phrase = "一、项目名称：首创证券新增代销机构-广州农商行"
    
    for i, chunk in enumerate(chunks):
        if target_phrase in chunk:
            print(f"\n   📋 Chunk {i+1} (包含目标短语):")
            print(f"      长度: {len(chunk)} 字符")
            
            # 查找这个短语在chunk中的位置
            start_pos = chunk.find(target_phrase)
            end_pos = start_pos + 100  # 显示短语后100字符
            
            context = chunk[max(0, start_pos-50):end_pos]
            print(f"      上下文: ...{context}...")
            
            # 检查chunk的来源（通过标题判断）
            lines = chunk.split('\n')
            for line in lines[:3]:  # 检查前3行
                if '>' in line or 'Part' in line:
                    print(f"      来源标识: {line}")
                    break


def analyze_table_extraction():
    """分析表格提取过程"""
    print("\n" + "=" * 80)
    print("🔍 分析表格提取过程")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    # 直接使用DocxSplitter来查看表格提取
    from contract_splitter.docx_splitter import DocxSplitter
    
    docx_splitter = DocxSplitter(max_tokens=1000, overlap=100)
    
    print("📄 直接使用DocxSplitter分析...")
    
    try:
        sections = docx_splitter.split(test_file)
        
        print(f"DocxSplitter得到 {len(sections)} 个sections")
        
        for i, section in enumerate(sections):
            content = section.get('content', '')
            if '一、项目名称' in content:
                print(f"\n📋 Section {i+1} 包含目标内容:")
                print(f"   标题: {section.get('heading', 'N/A')}")
                print(f"   内容长度: {len(content)}")
                
                # 计算目标短语出现次数
                target_count = content.count("一、项目名称：首创证券新增代销机构-广州农商行")
                print(f"   目标短语出现次数: {target_count}")
                
                if target_count > 1:
                    print("   ⚠️  在单个section中就有重复！")
                    
                    # 找到所有出现位置
                    positions = []
                    start = 0
                    while True:
                        pos = content.find("一、项目名称：首创证券新增代销机构-广州农商行", start)
                        if pos == -1:
                            break
                        positions.append(pos)
                        start = pos + 1
                    
                    print(f"   出现位置: {positions}")
                    
                    # 显示每个位置的上下文
                    for j, pos in enumerate(positions):
                        context_start = max(0, pos - 50)
                        context_end = min(len(content), pos + 150)
                        context = content[context_start:context_end]
                        print(f"   位置{j+1}上下文: ...{context}...")
    
    except Exception as e:
        print(f"❌ DocxSplitter分析失败: {e}")


def main():
    """主函数"""
    print("🚀 重复内容产生源头调试")
    print("=" * 80)
    
    debug_duplication_source()
    analyze_table_extraction()
    
    print("\n" + "=" * 80)
    print("🎯 调试完成")


if __name__ == "__main__":
    main()
