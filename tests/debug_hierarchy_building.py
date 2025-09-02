#!/usr/bin/env python3
"""
调试hierarchy building过程
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.docx_splitter import DocxSplitter


def debug_hierarchy_building():
    """调试hierarchy building过程"""
    print("🔍 调试hierarchy building过程")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 创建DocxSplitter
    splitter = DocxSplitter(max_tokens=2000, overlap=200)
    
    print("📄 步骤1: 提取elements")
    try:
        from contract_splitter.converter import DocumentConverter
        
        converter = DocumentConverter(cleanup_temp_files=False)
        docx_path = converter.convert_to_docx(test_file)
        
        from docx import Document
        doc = Document(docx_path)
        
        elements = splitter._extract_elements(doc)
        
        print(f"✅ 提取了 {len(elements)} 个elements")
        
        # 重点关注table cell elements
        table_cell_elements = []
        for i, elem in enumerate(elements):
            if elem.get('source', '').startswith('table_cell'):
                table_cell_elements.append((i, elem))
                print(f"\n📋 Table Cell Element {i}:")
                print(f"   text length: {len(elem.get('text', ''))}")
                print(f"   text preview: {elem.get('text', '')[:100]}...")
                print(f"   is_heading: {elem.get('is_heading', False)}")
                print(f"   level: {elem.get('level', 'N/A')}")
                print(f"   type: {elem.get('type', 'N/A')}")
                print(f"   source: {elem.get('source', 'N/A')}")
        
        print(f"\n📄 步骤2: 手动调试_build_hierarchy")
        
        # 手动模拟_build_hierarchy的关键部分
        sections = []
        current_section = None
        section_stack = []
        
        for i, element in enumerate(elements):
            print(f"\n--- Processing Element {i} ---")
            print(f"is_heading: {element.get('is_heading', False)}")
            print(f"level: {element.get('level', 'N/A')}")
            print(f"text: {element.get('text', '')[:50]}...")
            
            if element.get('is_heading', False):
                print("  → Creating new section (heading)")
                section = {
                    'heading': element['text'],
                    'content': '',
                    'level': element.get('level', 1),
                    'subsections': []
                }
                
                # 简化的层次处理
                if not sections:
                    sections.append(section)
                    current_section = section
                    section_stack = [section]
                else:
                    # 添加为subsection
                    if current_section:
                        current_section['subsections'].append(section)
                    else:
                        sections.append(section)
                    current_section = section
                    section_stack.append(section)
                
                print(f"  → Current section: {section['heading'][:30]}...")
            else:
                print("  → Adding content to current section")
                if current_section is not None:
                    print(f"  → Current section exists: {current_section['heading'][:30]}...")
                    if current_section['content']:
                        current_section['content'] += '\n\n' + element['text']
                        print(f"  → Appended content, new length: {len(current_section['content'])}")
                    else:
                        current_section['content'] = element['text']
                        print(f"  → Set content, length: {len(current_section['content'])}")
                else:
                    print("  → No current section!")
                    if not sections:
                        print("  → Creating default section")
                        sections.append({
                            'heading': 'Document Content',
                            'content': element['text'],
                            'level': 1,
                            'subsections': []
                        })
                        current_section = sections[0]
                        section_stack = [current_section]
        
        print(f"\n📄 步骤3: 分析最终sections")
        for i, section in enumerate(sections):
            print(f"\n📋 Section {i+1}:")
            print(f"   heading: {section.get('heading', 'N/A')}")
            print(f"   content length: {len(section.get('content', ''))}")
            print(f"   subsections: {len(section.get('subsections', []))}")
            
            if section.get('content'):
                preview = section['content'][:200].replace('\n', ' ')
                print(f"   content preview: {preview}...")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🚀 Hierarchy Building调试")
    print("=" * 80)
    
    debug_hierarchy_building()
    
    print("\n" + "=" * 80)
    print("🎯 调试完成")


if __name__ == "__main__":
    main()
