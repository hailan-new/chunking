#!/usr/bin/env python3
"""
分析内容结构，理解真实的标题vs列表
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.docx_splitter import DocxSplitter


def analyze_content_structure():
    """分析内容结构"""
    print("🔍 分析内容结构")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 创建DocxSplitter
    splitter = DocxSplitter(max_tokens=2000, overlap=200)
    
    print("📄 提取并分析table cell内容结构")
    try:
        from contract_splitter.converter import DocumentConverter
        
        converter = DocumentConverter(cleanup_temp_files=False)
        docx_path = converter.convert_to_docx(test_file)
        
        from docx import Document
        doc = Document(docx_path)
        
        # 找到包含大内容的table cell
        for table_idx, table in enumerate(doc.tables):
            for i, row in enumerate(table.rows):
                for j, cell in enumerate(row.cells):
                    cell_content = splitter._extract_nested_tables_from_cell(cell)
                    
                    if cell_content and len(cell_content) > 3000:
                        print(f"\n🎯 分析大cell ({i+1},{j+1}): {len(cell_content)} 字符")
                        
                        # 按层次标记分割
                        sections = splitter._split_by_hierarchy_markers_in_text(cell_content)
                        
                        print(f"\n📋 分割后的sections ({len(sections)}个):")
                        
                        for k, section in enumerate(sections):
                            print(f"\n--- Section {k+1} ---")
                            print(f"长度: {len(section)} 字符")
                            print(f"前100字符: {section[:100]}...")
                            
                            # 分析结构特征
                            print(f"结构分析:")
                            
                            # 1. 检查是否以标题标记开头
                            title_markers = ['一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、']
                            list_markers = ['（一）', '（二）', '（三）', '（四）', '（五）', '（六）', '（七）', '（八）', '（九）', '（十）']
                            
                            starts_with_title = any(section.startswith(marker) for marker in title_markers)
                            starts_with_list = any(section.startswith(marker) for marker in list_markers)
                            
                            if starts_with_title:
                                print(f"  ✅ 以大标题标记开头")
                            elif starts_with_list:
                                print(f"  📝 以列表标记开头")
                            else:
                                print(f"  ❓ 无明显标记")
                            
                            # 2. 检查是否包含冒号（列表特征）
                            has_colon = '：' in section[:50] or ':' in section[:50]
                            if has_colon:
                                print(f"  📝 包含冒号（可能是列表引导）")
                            
                            # 3. 检查内容密度
                            lines = [line.strip() for line in section.split('\n') if line.strip()]
                            if len(lines) > 3:
                                print(f"  📄 多行内容 ({len(lines)}行) - 可能是段落")
                            else:
                                print(f"  📝 简短内容 ({len(lines)}行) - 可能是标题")
                            
                            # 4. 检查是否包含详细描述
                            has_detailed_content = any(len(line) > 30 for line in lines)
                            if has_detailed_content:
                                print(f"  📄 包含详细描述 - 应该是内容段落")
                            else:
                                print(f"  📝 内容简短 - 可能是标题")
                            
                            # 5. 综合判断
                            print(f"  💡 建议处理方式:")
                            if starts_with_title and len(section) < 100:
                                print(f"     → 作为标题，但内容也要保留")
                            elif starts_with_list and has_colon:
                                print(f"     → 作为列表项内容，不是标题")
                            elif has_detailed_content:
                                print(f"     → 作为内容段落，不是标题")
                            else:
                                print(f"     → 需要更多上下文判断")
                        
                        return  # 只分析第一个大cell
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🚀 内容结构分析")
    print("=" * 80)
    
    analyze_content_structure()
    
    print("\n" + "=" * 80)
    print("🎯 分析完成")


if __name__ == "__main__":
    main()
