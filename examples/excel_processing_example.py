#!/usr/bin/env python3
"""
Excel文件处理示例
演示如何使用Contract Splitter的三大核心接口处理Excel文件
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def demo_excel_text_extraction():
    """演示接口3: Excel文本提取"""
    print("📊 接口3: Excel文本提取")
    print("=" * 60)
    
    from contract_splitter import SplitterFactory
    
    # 创建示例Excel文件
    import pandas as pd
    import tempfile
    import os
    
    # 示例法律条文数据
    legal_data = {
        '条文编号': ['第一条', '第二条', '第三条', '第四条'],
        '条文内容': [
            '为了规范证券公司分类监管，合理配置监管资源，提高监管效率，促进证券业健康发展，制定本规定。',
            '本规定适用于在中华人民共和国境内依法设立的证券公司。',
            '中国证监会及其派出机构依照本规定对证券公司进行分类监管。',
            '证券公司分类监管是指中国证监会根据证券公司风险管理能力、持续合规状况等因素进行的分类管理。'
        ],
        '适用范围': ['全部证券公司', '境内证券公司', '全部证券公司', '全部证券公司'],
        '监管部门': ['中国证监会', '中国证监会', '中国证监会及派出机构', '中国证监会']
    }
    
    # 创建多工作表Excel文件
    temp_file = tempfile.mktemp(suffix='.xlsx')
    
    with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
        # 法律条文工作表
        df_legal = pd.DataFrame(legal_data)
        df_legal.to_excel(writer, sheet_name='法律条文', index=False)
        
        # 监管指标工作表
        indicator_data = {
            '指标类别': ['风险管理', '合规状况', '市场竞争力'],
            '指标名称': ['净资本充足率', '合规检查结果', '营业收入'],
            '评分标准': ['优秀≥150%', '无重大违规', '行业前20%'],
            '权重': ['30%', '40%', '30%']
        }
        df_indicator = pd.DataFrame(indicator_data)
        df_indicator.to_excel(writer, sheet_name='监管指标', index=False)
    
    try:
        print(f"📄 处理Excel文件: {Path(temp_file).name}")
        
        # 1. 自动格式检测
        factory = SplitterFactory()
        file_format = factory.detect_file_format(temp_file)
        print(f"   🔍 检测格式: .{file_format}")
        
        # 2. 创建Excel分割器
        splitter = factory.create_splitter(temp_file)
        print(f"   🏭 使用分割器: {type(splitter).__name__}")
        
        # 3. 提取文本内容
        sections = splitter.split(temp_file)
        
        # 4. 分析提取结果
        print(f"   📊 提取结果:")
        print(f"      - Sections数量: {len(sections)}")
        
        total_text = ""
        for section in sections:
            total_text += section.content + "\n"
        
        print(f"      - 总文本长度: {len(total_text)} 字符")
        print(f"      - 平均section长度: {len(total_text) / len(sections):.0f} 字符")
        
        # 5. 显示各工作表内容
        print(f"   📋 工作表内容:")
        for i, section in enumerate(sections, 1):
            sheet_name = section.metadata.get('sheet_name', f'Sheet{i}')
            section_type = section.metadata.get('type', 'unknown')
            print(f"      工作表 {i}: {sheet_name} ({section_type})")
            print(f"         长度: {len(section.content)} 字符")
            
            # 显示内容预览
            content_preview = section.content[:150] + "..." if len(section.content) > 150 else section.content
            print(f"         预览: {content_preview}")
        
        # 6. 检查法律条文识别
        legal_sections = 0
        for section in sections:
            if "第" in section.content and "条" in section.content:
                legal_sections += 1
        
        print(f"   ⚖️ 法律条文识别: {legal_sections} 个sections包含法律条文")
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def demo_excel_sentence_chunking():
    """演示接口2: Excel句子完整性分块"""
    print("\n\n✂️ 接口2: Excel句子完整性分块")
    print("=" * 60)
    
    from contract_splitter import simple_chunk_file
    
    # 创建包含长条文的Excel文件
    import pandas as pd
    import tempfile
    import os
    
    # 长条文数据
    long_articles = {
        '条文编号': ['第一条', '第二条', '第三条'],
        '条文内容': [
            '为了规范证券公司分类监管，合理配置监管资源，提高监管效率，促进证券业健康发展，根据《中华人民共和国证券法》、《证券公司监督管理条例》等有关法律、行政法规的规定，制定本规定。本规定的制定旨在建立科学、合理的证券公司分类监管体系。',
            '本规定适用于在中华人民共和国境内依法设立的证券公司。证券公司应当按照本规定的要求，配合中国证监会及其派出机构开展分类评价工作。证券公司应当确保提供的信息真实、准确、完整。',
            '中国证监会及其派出机构依照本规定对证券公司进行分类监管。分类监管应当遵循公开、公平、公正的原则，确保监管标准的统一性和监管措施的有效性。监管部门应当定期评估分类监管的效果。'
        ]
    }
    
    temp_file = tempfile.mktemp(suffix='.xlsx')
    df = pd.DataFrame(long_articles)
    df.to_excel(temp_file, index=False, sheet_name='长条文')
    
    try:
        print(f"📄 处理Excel文件: {Path(temp_file).name}")
        
        # 测试不同的分块参数
        chunk_configs = [
            {"max_chunk_size": 150, "overlap_ratio": 0.1, "name": "小块分块"},
            {"max_chunk_size": 300, "overlap_ratio": 0.15, "name": "中块分块"},
            {"max_chunk_size": 500, "overlap_ratio": 0.2, "name": "大块分块"},
        ]
        
        for config in chunk_configs:
            print(f"\n🔧 {config['name']} (max_size={config['max_chunk_size']}, overlap={config['overlap_ratio']})")
            
            # 句子完整性分块
            chunks = simple_chunk_file(
                temp_file,
                max_chunk_size=config['max_chunk_size'],
                overlap_ratio=config['overlap_ratio']
            )
            
            # 分析结果
            chunk_sizes = [len(chunk['content']) for chunk in chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            
            print(f"   📊 结果: {len(chunks)} 个chunks, 平均{avg_size:.0f}字符")
            
            # 检查句子完整性
            complete_sentences = 0
            for chunk in chunks:
                content = chunk['content'].strip()
                if content.endswith(('。', '！', '？', '；', '.', '!', '?', ';')):
                    complete_sentences += 1
            
            completion_rate = complete_sentences / len(chunks) * 100
            print(f"   ✅ 句子完整率: {completion_rate:.1f}% ({complete_sentences}/{len(chunks)})")
            
            # 显示第一个chunk示例
            if chunks:
                first_chunk = chunks[0]['content']
                preview = first_chunk[:120] + "..." if len(first_chunk) > 120 else first_chunk
                print(f"   📝 首个chunk: {preview}")
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def demo_excel_hierarchical_chunking():
    """演示接口1: Excel层次化分块"""
    print("\n\n📊 接口1: Excel层次化分块")
    print("=" * 60)
    
    from contract_splitter import split_document, flatten_sections
    
    # 创建具有层次结构的Excel文件
    import pandas as pd
    import tempfile
    import os
    
    # 创建多工作表，模拟层次结构
    temp_file = tempfile.mktemp(suffix='.xlsx')
    
    with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
        # 第一章 - 总则
        chapter1_data = {
            '条文': ['第一条', '第二条'],
            '内容': [
                '为了规范证券公司分类监管，制定本规定。',
                '本规定适用于境内证券公司。'
            ]
        }
        df1 = pd.DataFrame(chapter1_data)
        df1.to_excel(writer, sheet_name='第一章_总则', index=False)
        
        # 第二章 - 分类评价
        chapter2_data = {
            '条文': ['第三条', '第四条', '第五条'],
            '内容': [
                '中国证监会进行分类监管。',
                '分类监管基于风险管理能力。',
                '评价每年进行一次。'
            ]
        }
        df2 = pd.DataFrame(chapter2_data)
        df2.to_excel(writer, sheet_name='第二章_分类评价', index=False)
        
        # 附录 - 评价标准
        appendix_data = {
            '指标': ['净资本充足率', '合规状况'],
            '标准': ['≥150%为优秀', '无违规为优秀']
        }
        df3 = pd.DataFrame(appendix_data)
        df3.to_excel(writer, sheet_name='附录_评价标准', index=False)
    
    try:
        print(f"📄 处理Excel文件: {Path(temp_file).name}")
        
        # 1. 层次化分块
        sections = split_document(temp_file, max_tokens=200)
        print(f"   📊 层次化分块: {len(sections)} 个sections")
        
        # 显示层次结构
        print(f"   📋 文档层次结构:")
        for i, section in enumerate(sections, 1):
            level = getattr(section, 'level', 0)
            sheet_name = section.metadata.get('sheet_name', 'Unknown')
            content_preview = section.content[:80] + "..." if len(section.content) > 80 else section.content
            print(f"      {i}. Level {level} - {sheet_name}: {content_preview}")
        
        # 2. 测试不同的扁平化策略
        strategies = [
            ("finest_granularity", "最细粒度"),
            ("all_levels", "所有层级"),
            ("parent_only", "仅父级")
        ]
        
        for strategy, description in strategies:
            print(f"\n   🔧 扁平化策略: {strategy} ({description})")
            chunks = flatten_sections(sections, strategy=strategy)
            print(f"      结果: {len(chunks)} 个chunks")
            
            # 显示前2个chunks
            for j, chunk in enumerate(chunks[:2], 1):
                level = getattr(chunk, 'level', 0)
                content_preview = chunk.content[:60] + "..." if len(chunk.content) > 60 else chunk.content
                print(f"         Chunk {j} (Level {level}): {content_preview}")
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def demo_excel_advanced_features():
    """演示Excel高级功能"""
    print("\n\n🔧 Excel高级功能")
    print("=" * 60)
    
    from contract_splitter import ExcelSplitter
    
    # 创建复杂的Excel文件
    import pandas as pd
    import tempfile
    import os
    
    temp_file = tempfile.mktemp(suffix='.xlsx')
    
    with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
        # 包含公式的工作表
        formula_data = {
            '项目': ['收入', '成本', '利润'],
            '金额': [1000000, 800000, '=A2-A3'],  # 包含公式
            '比例': ['=B2/B2', '=B3/B2', '=B4/B2']
        }
        df_formula = pd.DataFrame(formula_data)
        df_formula.to_excel(writer, sheet_name='财务数据', index=False)
        
        # 包含合并单元格的工作表
        merged_data = {
            '大类': ['风险指标', '风险指标', '合规指标', '合规指标'],
            '小类': ['净资本', '流动性', '违规次数', '整改情况'],
            '标准': ['≥150%', '≥120%', '0次', '及时整改']
        }
        df_merged = pd.DataFrame(merged_data)
        df_merged.to_excel(writer, sheet_name='评价指标', index=False)
    
    try:
        print(f"📄 处理复杂Excel文件: {Path(temp_file).name}")
        
        # 测试不同的提取模式
        extract_modes = [
            ("legal_content", "法律内容模式"),
            ("table_structure", "表格结构模式"),
            ("all_content", "全部内容模式")
        ]
        
        for mode, description in extract_modes:
            print(f"\n🔧 提取模式: {mode} ({description})")
            
            splitter = ExcelSplitter(
                max_tokens=300,
                extract_mode=mode
            )
            
            sections = splitter.split(temp_file)
            print(f"   📊 结果: {len(sections)} 个sections")
            
            for i, section in enumerate(sections, 1):
                sheet_name = section.metadata.get('sheet_name', 'Unknown')
                section_type = section.metadata.get('type', 'unknown')
                print(f"      Section {i}: {sheet_name} ({section_type})")
                print(f"         长度: {len(section.content)} 字符")
                
                # 显示内容预览
                content_preview = section.content[:100] + "..." if len(section.content) > 100 else section.content
                print(f"         内容: {content_preview}")
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def main():
    """主函数"""
    print("📊 Excel文件处理示例")
    print("=" * 80)
    print("本示例演示如何使用Contract Splitter的三大核心接口处理Excel文件")
    
    # 演示三大核心接口在Excel处理中的应用
    demo_excel_text_extraction()      # 接口3: 文本提取
    demo_excel_sentence_chunking()     # 接口2: 句子完整性分块
    demo_excel_hierarchical_chunking() # 接口1: 层次化分块
    demo_excel_advanced_features()     # 高级功能
    
    print(f"\n🎉 Excel文件处理示例完成")
    print("=" * 80)
    print("💡 Excel处理最佳实践:")
    print("1. 使用SplitterFactory自动检测和处理Excel格式")
    print("2. 根据内容类型选择合适的extract_mode")
    print("3. 对于法律条文Excel，使用legal_content模式")
    print("4. 句子完整性分块特别适合处理长条文内容")
    print("5. 层次化分块可以保持多工作表的逻辑结构")
    print("6. 支持复杂Excel特性：公式、合并单元格等")


if __name__ == "__main__":
    main()
