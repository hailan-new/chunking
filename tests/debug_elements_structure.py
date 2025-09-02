#!/usr/bin/env python3
"""
调试elements结构
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.docx_splitter import DocxSplitter


def debug_elements_structure():
    """调试elements结构"""
    print("🔍 调试elements结构")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 创建DocxSplitter
    splitter = DocxSplitter(max_tokens=2000, overlap=200)
    
    print("📄 调用_extract_elements方法")
    try:
        # 直接调用内部方法来查看elements
        from contract_splitter.converter import DocumentConverter
        
        converter = DocumentConverter(cleanup_temp_files=False)
        docx_path = converter.convert_to_docx(test_file)
        
        from docx import Document
        doc = Document(docx_path)
        
        elements = splitter._extract_elements(doc)
        
        print(f"✅ 提取了 {len(elements)} 个elements")
        
        # 分析每个element
        for i, elem in enumerate(elements):
            print(f"\n📋 Element {i+1}:")
            print(f"   text: {elem.get('text', '')[:100]}...")
            print(f"   style: {elem.get('style', 'N/A')}")
            print(f"   is_heading: {elem.get('is_heading', False)}")
            print(f"   level: {elem.get('level', 'N/A')}")
            print(f"   type: {elem.get('type', 'N/A')}")
            print(f"   source: {elem.get('source', 'N/A')}")
        
        print(f"\n📄 调用_build_hierarchy方法")
        sections = splitter._build_hierarchy(elements)
        
        print(f"✅ 构建了 {len(sections)} 个sections")
        
        # 分析每个section
        for i, section in enumerate(sections):
            print(f"\n📋 Section {i+1}:")
            print(f"   heading: {section.get('heading', 'N/A')}")
            print(f"   content length: {len(section.get('content', ''))}")
            print(f"   subsections: {len(section.get('subsections', []))}")
            
            # 显示subsections
            for j, subsection in enumerate(section.get('subsections', [])):
                print(f"     Subsection {j+1}: {subsection.get('heading', 'N/A')[:50]}...")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🚀 Elements结构调试")
    print("=" * 80)
    
    debug_elements_structure()
    
    print("\n" + "=" * 80)
    print("🎯 调试完成")


if __name__ == "__main__":
    main()
