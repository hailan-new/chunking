#!/usr/bin/env python3
"""
调试subsections内容
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.docx_splitter import DocxSplitter


def debug_subsections():
    """调试subsections内容"""
    print("🔍 调试subsections内容")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 创建DocxSplitter
    splitter = DocxSplitter(max_tokens=2000, overlap=200)
    
    print("📄 调用split方法获取完整sections")
    try:
        sections = splitter.split(test_file)
        
        print(f"✅ 得到 {len(sections)} 个sections")
        
        def print_section_tree(section_list, indent=0):
            """递归打印section树结构"""
            for i, section in enumerate(section_list):
                prefix = "  " * indent
                heading = section.get('heading', 'N/A')
                content_length = len(section.get('content', ''))
                subsections_count = len(section.get('subsections', []))
                
                print(f"{prefix}📋 Section {i+1}: {heading[:50]}...")
                print(f"{prefix}   Content length: {content_length}")
                print(f"{prefix}   Subsections: {subsections_count}")
                
                if content_length > 0:
                    content_preview = section['content'][:200].replace('\n', ' ')
                    print(f"{prefix}   Content preview: {content_preview}...")
                
                # 递归处理subsections
                if section.get('subsections'):
                    print(f"{prefix}   Subsections:")
                    print_section_tree(section['subsections'], indent + 1)
        
        print("\n📊 完整的sections树结构:")
        print_section_tree(sections)
        
        print(f"\n📄 测试flatten方法")
        chunks = splitter.flatten(sections)
        print(f"✅ 得到 {len(chunks)} 个chunks")
        
        for i, chunk in enumerate(chunks):
            print(f"\n📋 Chunk {i+1}:")
            print(f"   长度: {len(chunk)} 字符")
            
            if "一、项目名称" in chunk:
                print(f"   ✅ 包含项目名称")
            if "广州金融控股" in chunk:
                print(f"   ✅ 包含股东信息")
            
            preview = chunk[:200].replace('\n', ' ')
            print(f"   预览: {preview}...")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🚀 Subsections调试")
    print("=" * 80)
    
    debug_subsections()
    
    print("\n" + "=" * 80)
    print("🎯 调试完成")


if __name__ == "__main__":
    main()
