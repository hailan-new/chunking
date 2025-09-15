#!/usr/bin/env python3
"""
Contract Splitter 基础使用示例
演示三大核心接口的基本用法
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def demo_hierarchical_chunking():
    """演示接口1: 层次化分块接口"""
    print("🎯 接口1: 层次化分块接口")
    print("=" * 60)
    
    from contract_splitter import split_document, flatten_sections
    
    # 示例文档路径（请替换为实际文档路径）
    document_path = "output/law/附件1.关于修改《证券公司分类监管规定》的决定.pdf"
    
    if not Path(document_path).exists():
        print(f"⚠️ 示例文档不存在: {document_path}")
        print("请将您的文档放在该路径，或修改document_path变量")
        return
    
    try:
        print(f"📄 处理文档: {Path(document_path).name}")
        
        # 1. 层次化分块
        print("\n🔍 步骤1: 层次化分块")
        sections = split_document(document_path, max_tokens=1000)
        
        print(f"✅ 分块完成: {len(sections)} 个层次化sections")
        
        # 显示层次结构
        print("\n📊 文档层次结构:")
        for i, section in enumerate(sections[:5], 1):  # 只显示前5个
            level = getattr(section, 'level', 0)
            title = getattr(section, 'title', 'Unknown')
            content_preview = section.content[:50] + "..." if len(section.content) > 50 else section.content
            print(f"  {i}. Level {level}: {title}")
            print(f"     内容: {content_preview}")
        
        if len(sections) > 5:
            print(f"     ... 还有 {len(sections) - 5} 个sections")
        
        # 2. 扁平化处理 - 不同策略对比
        print(f"\n🔧 步骤2: 扁平化处理")
        
        strategies = [
            ("finest_granularity", "最细粒度 - 获取最小的文档单元"),
            ("all_levels", "所有层级 - 包含各层级的完整内容"),
            ("parent_only", "仅父级 - 只保留顶级sections")
        ]
        
        for strategy, description in strategies:
            print(f"\n📋 策略: {strategy} ({description})")
            chunks = flatten_sections(sections, strategy=strategy)
            print(f"   结果: {len(chunks)} 个chunks")
            
            # 显示前2个chunks的示例
            for i, chunk in enumerate(chunks[:2], 1):
                level = getattr(chunk, 'level', 0)
                content_preview = chunk.content[:80] + "..." if len(chunk.content) > 80 else chunk.content
                print(f"   Chunk {i} (Level {level}): {content_preview}")
        
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")


def demo_sentence_integrity_chunking():
    """演示接口2: 句子完整性分块接口"""
    print("\n\n🎯 接口2: 句子完整性分块接口")
    print("=" * 60)
    
    from contract_splitter import simple_chunk_file
    
    # 示例文档路径
    document_path = "output/law/附件1.期货公司互联网营销管理暂行规定.pdf"
    
    if not Path(document_path).exists():
        print(f"⚠️ 示例文档不存在: {document_path}")
        print("请将您的文档放在该路径，或修改document_path变量")
        return
    
    try:
        print(f"📄 处理文档: {Path(document_path).name}")
        
        # 测试不同的分块参数
        test_configs = [
            {"max_chunk_size": 300, "overlap_ratio": 0.1, "name": "小块 (300字符, 10%重叠)"},
            {"max_chunk_size": 600, "overlap_ratio": 0.15, "name": "中块 (600字符, 15%重叠)"},
            {"max_chunk_size": 1000, "overlap_ratio": 0.2, "name": "大块 (1000字符, 20%重叠)"},
        ]
        
        for config in test_configs:
            print(f"\n🔧 配置: {config['name']}")
            
            # 句子完整性分块
            chunks = simple_chunk_file(
                document_path,
                max_chunk_size=config['max_chunk_size'],
                overlap_ratio=config['overlap_ratio']
            )
            
            # 分析结果
            chunk_sizes = [len(chunk['content']) for chunk in chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            max_size = max(chunk_sizes)
            min_size = min(chunk_sizes)
            
            print(f"   📊 结果: {len(chunks)} 个chunks")
            print(f"   📏 大小: 平均{avg_size:.0f}, 最大{max_size}, 最小{min_size} 字符")
            
            # 检查句子完整性
            complete_sentences = 0
            for chunk in chunks:
                content = chunk['content'].strip()
                if content.endswith(('。', '！', '？', '；', '.', '!', '?', ';')):
                    complete_sentences += 1
            
            completion_rate = complete_sentences / len(chunks) * 100
            print(f"   ✅ 句子完整率: {completion_rate:.1f}% ({complete_sentences}/{len(chunks)})")
            
            # 显示前2个chunks示例
            print(f"   📝 示例chunks:")
            for i, chunk in enumerate(chunks[:2], 1):
                content_preview = chunk['content'][:100] + "..." if len(chunk['content']) > 100 else chunk['content']
                print(f"      Chunk {i}: {content_preview}")
        
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")


def demo_text_extraction():
    """演示接口3: 多格式文本提取接口"""
    print("\n\n🎯 接口3: 多格式文本提取接口")
    print("=" * 60)
    
    from contract_splitter import SplitterFactory
    import os
    
    # 测试不同格式的文档
    test_files = [
        ("output/law/附件1.关于修改《证券公司分类监管规定》的决定.pdf", "PDF文档"),
        ("output/law/9147de404f6d4df986b0cb41acd47aac.wps", "WPS文档"),
        # 可以添加更多格式的测试文件
    ]
    
    factory = SplitterFactory()
    
    for file_path, file_type in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️ {file_type}不存在: {file_path}")
            continue
        
        try:
            print(f"\n📄 处理{file_type}: {Path(file_path).name}")
            
            # 1. 自动格式检测
            file_format = factory.detect_file_format(file_path)
            print(f"   🔍 检测格式: .{file_format}")
            
            # 2. 创建合适的分割器
            splitter = factory.create_splitter(file_path)
            print(f"   🏭 使用分割器: {type(splitter).__name__}")
            
            # 3. 提取文本内容
            sections = splitter.split(file_path)
            
            # 4. 合并为完整文本
            full_text = "\n".join([section.content for section in sections])
            
            # 5. 分析提取结果
            print(f"   📊 提取结果:")
            print(f"      - Sections数量: {len(sections)}")
            print(f"      - 总文本长度: {len(full_text)} 字符")
            print(f"      - 平均section长度: {len(full_text) / len(sections):.0f} 字符")
            
            # 6. 显示文本预览
            print(f"   📝 文本预览:")
            preview_text = full_text[:200] + "..." if len(full_text) > 200 else full_text
            print(f"      {preview_text}")
            
            # 7. 检查文本质量
            chinese_chars = sum(1 for char in full_text if '\u4e00' <= char <= '\u9fff')
            chinese_ratio = chinese_chars / len(full_text) * 100 if full_text else 0
            print(f"   🇨🇳 中文字符比例: {chinese_ratio:.1f}%")
            
        except Exception as e:
            print(f"   ❌ 处理失败: {str(e)}")


def demo_advanced_usage():
    """演示高级用法"""
    print("\n\n🎯 高级用法示例")
    print("=" * 60)
    
    # 1. 法律文档专业处理
    print("📚 法律文档专业处理:")
    try:
        from contract_splitter.domain_helpers import split_legal_document
        
        legal_doc = "output/law/附件1.关于修改《证券公司分类监管规定》的决定.pdf"
        if Path(legal_doc).exists():
            chunks = split_legal_document(legal_doc, max_tokens=800)
            print(f"   ✅ 法律文档分块: {len(chunks)} 个条文块")
            
            # 显示第一个条文块
            if chunks:
                first_chunk = chunks[0][:150] + "..." if len(chunks[0]) > 150 else chunks[0]
                print(f"   📝 第一个条文块: {first_chunk}")
        else:
            print(f"   ⚠️ 法律文档不存在: {legal_doc}")
    except Exception as e:
        print(f"   ❌ 法律文档处理失败: {str(e)}")
    
    # 2. 自定义分块策略
    print(f"\n🔧 自定义分块策略:")
    try:
        from contract_splitter.utils import sliding_window_split
        
        sample_text = "第一条 这是一个测试条文。第二条 这是另一个测试条文。第三条 这是第三个测试条文，内容稍微长一些。"
        
        # 句子优先分块
        chunks = sliding_window_split(
            sample_text,
            max_tokens=50,
            overlap=10,
            by_sentence=True,
            token_counter="character"
        )
        
        print(f"   ✅ 自定义分块: {len(chunks)} 个chunks")
        for i, chunk in enumerate(chunks, 1):
            print(f"   Chunk {i} ({len(chunk)}字符): {chunk}")
            
    except Exception as e:
        print(f"   ❌ 自定义分块失败: {str(e)}")


def main():
    """主函数"""
    print("🚀 Contract Splitter 基础使用示例")
    print("=" * 80)
    print("本示例演示三大核心接口的基本用法")
    print("请确保在output/law目录下有测试文档")
    
    # 演示三大核心接口
    demo_hierarchical_chunking()
    demo_sentence_integrity_chunking()
    demo_text_extraction()
    demo_advanced_usage()
    
    print(f"\n🎉 示例演示完成")
    print("=" * 80)
    print("💡 提示:")
    print("1. 根据文档类型选择合适的分块策略")
    print("2. 调整参数以获得最佳分块效果")
    print("3. 法律文档建议使用专业的法律分块接口")
    print("4. 查看examples目录获取更多专业示例")


if __name__ == "__main__":
    main()
