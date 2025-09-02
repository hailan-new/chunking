#!/usr/bin/env python3
"""
调试table cell分割过程
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.docx_splitter import DocxSplitter


def debug_table_cell_split():
    """调试table cell分割过程"""
    print("🔍 调试table cell分割过程")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 创建DocxSplitter
    splitter = DocxSplitter(max_tokens=2000, overlap=200)
    
    print("📄 提取大table cell内容并测试分割")
    try:
        from contract_splitter.converter import DocumentConverter
        
        converter = DocumentConverter(cleanup_temp_files=False)
        docx_path = converter.convert_to_docx(test_file)
        
        from docx import Document
        doc = Document(docx_path)
        
        # 找到包含大内容的table cell
        for table_idx, table in enumerate(doc.tables):
            print(f"\n📋 Table {table_idx + 1}:")
            for i, row in enumerate(table.rows):
                for j, cell in enumerate(row.cells):
                    cell_content = splitter._extract_nested_tables_from_cell(cell)
                    
                    if cell_content and len(cell_content) > 3000:
                        print(f"\n🎯 找到大cell ({i+1},{j+1}): {len(cell_content)} 字符")
                        
                        # 显示前500字符
                        print(f"前500字符: {cell_content[:500]}...")
                        
                        # 测试_split_cell_content_as_document方法
                        print(f"\n🔧 测试_split_cell_content_as_document:")
                        elements = splitter._split_cell_content_as_document(cell_content, i, j)
                        print(f"分割后elements数量: {len(elements)}")
                        
                        for k, elem in enumerate(elements):
                            print(f"\n  Element {k+1}:")
                            print(f"    is_heading: {elem.get('is_heading')}")
                            print(f"    level: {elem.get('level')}")
                            print(f"    text length: {len(elem.get('text', ''))}")
                            text_preview = elem.get('text', '')[:100].replace('\n', ' ')
                            print(f"    text preview: {text_preview}...")
                        
                        # 测试_is_clear_heading_line方法
                        print(f"\n🔧 测试_is_clear_heading_line:")
                        lines = [line.strip() for line in cell_content.split('\n') if line.strip()]
                        print(f"总行数: {len(lines)}")
                        
                        heading_lines = []
                        for line_idx, line in enumerate(lines[:10]):  # 只检查前10行
                            is_heading = splitter._is_clear_heading_line(line)
                            print(f"  行{line_idx+1} ({len(line)}字符): {is_heading} - {line[:50]}...")
                            if is_heading:
                                heading_lines.append(line)
                        
                        print(f"识别为标题的行数: {len(heading_lines)}")
                        
                        # 测试层次检测
                        print(f"\n🔧 测试层次标记检测:")
                        hierarchy_markers = ['一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、']
                        for marker in hierarchy_markers:
                            if marker in cell_content:
                                pos = cell_content.find(marker)
                                context = cell_content[max(0, pos-20):pos+50]
                                print(f"  找到 '{marker}' at position {pos}: ...{context}...")
                        
                        return  # 只处理第一个大cell
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🚀 Table Cell分割调试")
    print("=" * 80)
    
    debug_table_cell_split()
    
    print("\n" + "=" * 80)
    print("🎯 调试完成")


if __name__ == "__main__":
    main()
