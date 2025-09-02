#!/usr/bin/env python3
"""
调试table cell内容
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.docx_splitter import DocxSplitter


def debug_table_cell_content():
    """调试table cell内容"""
    print("🔍 调试table cell内容")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 创建DocxSplitter
    splitter = DocxSplitter(max_tokens=2000, overlap=200)
    
    print("📄 提取table cell内容")
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
                    
                    if cell_content and len(cell_content) > 1000:
                        print(f"\n🎯 找到大cell ({i+1},{j+1}): {len(cell_content)} 字符")
                        print(f"前200字符: {cell_content[:200]}")
                        print(f"包含换行符数量: {cell_content.count(chr(10))}")
                        print(f"包含空格数量: {cell_content.count(' ')}")
                        
                        # 测试分割逻辑
                        lines = [line.strip() for line in cell_content.split('\n') if line.strip()]
                        print(f"分割后行数: {len(lines)}")
                        
                        for k, line in enumerate(lines[:5]):  # 只显示前5行
                            print(f"  行{k+1} ({len(line)}字符): {line[:100]}...")
                            
                            # 测试是否被识别为标题
                            is_heading = splitter._is_clear_heading_line(line)
                            print(f"    是否为标题: {is_heading}")
                        
                        # 测试我们的分割方法
                        print(f"\n🔧 测试_split_cell_content_as_document:")
                        elements = splitter._split_cell_content_as_document(cell_content, i, j)
                        print(f"分割后elements数量: {len(elements)}")
                        
                        for k, elem in enumerate(elements):
                            print(f"  Element {k+1}:")
                            print(f"    is_heading: {elem.get('is_heading')}")
                            print(f"    level: {elem.get('level')}")
                            print(f"    text length: {len(elem.get('text', ''))}")
                            print(f"    text preview: {elem.get('text', '')[:100]}...")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🚀 Table Cell内容调试")
    print("=" * 80)
    
    debug_table_cell_content()
    
    print("\n" + "=" * 80)
    print("🎯 调试完成")


if __name__ == "__main__":
    main()
