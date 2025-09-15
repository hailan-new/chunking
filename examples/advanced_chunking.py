#!/usr/bin/env python3
"""
高级分块策略示例
演示Contract Splitter的高级功能和自定义分块策略
"""

import sys
from pathlib import Path
import tempfile
import os

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def demo_sentence_priority_vs_strict_chunking():
    """演示句子优先分块 vs 严格字符分块的对比"""
    print("🎯 句子优先分块 vs 严格字符分块对比")
    print("=" * 60)
    
    from contract_splitter.utils import sliding_window_split
    
    # 测试文本 - 包含完整的法律条文
    test_text = """
    第一条 为了规范证券公司分类监管，合理配置监管资源，提高监管效率，促进证券业健康发展，根据《证券法》、《证券公司监督管理条例》等法律法规，制定本规定。第二条 本规定适用于在中华人民共和国境内依法设立的证券公司。第三条 中国证监会及其派出机构依照本规定对证券公司进行分类监管。第四条 证券公司分类监管是指中国证监会根据证券公司风险管理能力、持续合规状况等因素，将证券公司分为不同类别，并据此对证券公司实施差别化监管的制度。第五条 证券公司分类评价每年进行一次，评价基准日为每年的12月31日。评价结果有效期为一年。
    """.strip()
    
    print(f"📝 测试文本长度: {len(test_text)} 字符")
    
    # 测试配置
    max_tokens = 200
    overlap = 40
    
    print(f"\n🔧 测试配置: max_tokens={max_tokens}, overlap={overlap}")
    
    # 1. 句子优先分块 (推荐方式)
    print(f"\n✅ 句子优先分块 (推荐):")
    chunks_sentence = sliding_window_split(
        test_text,
        max_tokens=max_tokens,
        overlap=overlap,
        by_sentence=True,  # 句子优先
        token_counter="character"
    )
    
    sentence_complete = 0
    for i, chunk in enumerate(chunks_sentence, 1):
        ends_complete = chunk.strip().endswith(('。', '！', '？', '；', '.', '!', '?', ';'))
        if ends_complete:
            sentence_complete += 1
            status = "✅"
        else:
            status = "⚠️"
        
        print(f"   Chunk {i} ({len(chunk)}字符) {status}: {chunk[:80]}...")
        if not ends_complete:
            print(f"      结尾: ...{chunk[-30:]}")
    
    # 2. 严格字符分块 (传统方式)
    print(f"\n❌ 严格字符分块 (传统):")
    chunks_strict = sliding_window_split(
        test_text,
        max_tokens=max_tokens,
        overlap=overlap,
        by_sentence=False,  # 严格字符限制
        token_counter="character"
    )
    
    strict_complete = 0
    for i, chunk in enumerate(chunks_strict, 1):
        ends_complete = chunk.strip().endswith(('。', '！', '？', '；', '.', '!', '?', ';'))
        if ends_complete:
            strict_complete += 1
            status = "✅"
        else:
            status = "⚠️"
        
        print(f"   Chunk {i} ({len(chunk)}字符) {status}: {chunk[:80]}...")
        if not ends_complete:
            print(f"      结尾: ...{chunk[-30:]}")
    
    # 3. 对比结果
    print(f"\n📊 对比结果:")
    sentence_rate = sentence_complete / len(chunks_sentence) * 100
    strict_rate = strict_complete / len(chunks_strict) * 100
    improvement = sentence_rate - strict_rate
    
    print(f"   句子优先分块: {sentence_complete}/{len(chunks_sentence)} 完整 ({sentence_rate:.1f}%)")
    print(f"   严格字符分块: {strict_complete}/{len(chunks_strict)} 完整 ({strict_rate:.1f}%)")
    print(f"   🚀 改进幅度: +{improvement:.1f}% 句子完整率提升")


def demo_hierarchical_strategies():
    """演示不同的层次化分块策略"""
    print("\n\n📊 层次化分块策略对比")
    print("=" * 60)
    
    from contract_splitter import split_document, flatten_sections
    
    # 使用示例文档
    document_path = "output/law/附件1.关于修改《证券公司分类监管规定》的决定.pdf"
    
    if not Path(document_path).exists():
        print(f"⚠️ 示例文档不存在: {document_path}")
        return
    
    try:
        print(f"📄 处理文档: {Path(document_path).name}")
        
        # 获取层次化sections
        sections = split_document(document_path, max_tokens=800)
        print(f"   原始sections: {len(sections)} 个")
        
        # 测试不同的扁平化策略
        strategies = [
            ("finest_granularity", "最细粒度 - 获取最小的文档单元"),
            ("all_levels", "所有层级 - 包含各层级的完整内容"),
            ("parent_only", "仅父级 - 只保留顶级sections")
        ]
        
        for strategy, description in strategies:
            print(f"\n🔧 策略: {strategy}")
            print(f"   描述: {description}")
            
            chunks = flatten_sections(sections, strategy=strategy)
            
            # 分析结果
            chunk_sizes = [len(chunk.content) for chunk in chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            max_size = max(chunk_sizes) if chunk_sizes else 0
            min_size = min(chunk_sizes) if chunk_sizes else 0
            
            print(f"   📊 结果: {len(chunks)} 个chunks")
            print(f"   📏 大小: 平均{avg_size:.0f}, 最大{max_size}, 最小{min_size} 字符")
            
            # 显示层级分布
            level_distribution = {}
            for chunk in chunks:
                level = getattr(chunk, 'level', 0)
                level_distribution[level] = level_distribution.get(level, 0) + 1
            
            print(f"   📋 层级分布: {dict(sorted(level_distribution.items()))}")
            
            # 显示前2个chunks示例
            print(f"   📝 示例chunks:")
            for i, chunk in enumerate(chunks[:2], 1):
                level = getattr(chunk, 'level', 0)
                content_preview = chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
                print(f"      {i}. Level {level}: {content_preview}")
    
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")


def demo_custom_chunking_parameters():
    """演示自定义分块参数的效果"""
    print("\n\n🔧 自定义分块参数效果对比")
    print("=" * 60)
    
    from contract_splitter import simple_chunk_file
    
    # 使用示例文档
    document_path = "output/law/附件1.期货公司互联网营销管理暂行规定.pdf"
    
    if not Path(document_path).exists():
        print(f"⚠️ 示例文档不存在: {document_path}")
        return
    
    # 测试不同的参数组合
    parameter_sets = [
        {"max_chunk_size": 200, "overlap_ratio": 0.05, "name": "小块低重叠"},
        {"max_chunk_size": 200, "overlap_ratio": 0.25, "name": "小块高重叠"},
        {"max_chunk_size": 600, "overlap_ratio": 0.1, "name": "中块标准重叠"},
        {"max_chunk_size": 1200, "overlap_ratio": 0.15, "name": "大块适中重叠"},
    ]
    
    try:
        print(f"📄 测试文档: {Path(document_path).name}")
        
        for params in parameter_sets:
            print(f"\n🔧 参数组合: {params['name']}")
            print(f"   max_chunk_size: {params['max_chunk_size']}")
            print(f"   overlap_ratio: {params['overlap_ratio']}")
            
            chunks = simple_chunk_file(
                document_path,
                max_chunk_size=params['max_chunk_size'],
                overlap_ratio=params['overlap_ratio']
            )
            
            # 分析结果
            chunk_sizes = [len(chunk['content']) for chunk in chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            max_size = max(chunk_sizes)
            min_size = min(chunk_sizes)
            
            # 计算实际重叠
            total_chars = sum(chunk_sizes)
            original_size = len(open(document_path, 'rb').read())  # 近似原始大小
            
            print(f"   📊 结果:")
            print(f"      - Chunks数量: {len(chunks)}")
            print(f"      - 平均大小: {avg_size:.0f} 字符")
            print(f"      - 大小范围: {min_size} - {max_size} 字符")
            print(f"      - 总字符数: {total_chars}")
            
            # 检查句子完整性
            complete_sentences = sum(1 for chunk in chunks 
                                   if chunk['content'].strip().endswith(('。', '！', '？', '；', '.', '!', '?', ';')))
            completion_rate = complete_sentences / len(chunks) * 100
            print(f"      - 句子完整率: {completion_rate:.1f}%")
            
            # 显示第一个chunk示例
            if chunks:
                first_chunk = chunks[0]['content']
                preview = first_chunk[:120] + "..." if len(first_chunk) > 120 else first_chunk
                print(f"   📝 首个chunk: {preview}")
    
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")


def demo_token_counting_methods():
    """演示不同的token计数方法"""
    print("\n\n🔢 Token计数方法对比")
    print("=" * 60)
    
    from contract_splitter.utils import sliding_window_split, count_tokens
    
    # 测试文本
    test_text = "第一条 为了规范证券公司分类监管，合理配置监管资源，提高监管效率，促进证券业健康发展，制定本规定。"
    
    print(f"📝 测试文本: {test_text}")
    print(f"   文本长度: {len(test_text)} 字符")
    
    # 测试不同的计数方法
    counting_methods = ["character", "tiktoken"]
    
    for method in counting_methods:
        try:
            print(f"\n🔢 计数方法: {method}")
            
            # 计算token数
            token_count = count_tokens(test_text, method)
            print(f"   Token数量: {token_count}")
            
            # 使用该方法进行分块
            chunks = sliding_window_split(
                test_text,
                max_tokens=50,
                overlap=10,
                by_sentence=True,
                token_counter=method
            )
            
            print(f"   分块结果: {len(chunks)} 个chunks")
            for i, chunk in enumerate(chunks, 1):
                chunk_tokens = count_tokens(chunk, method)
                print(f"      Chunk {i}: {chunk_tokens} tokens, {len(chunk)} 字符")
                print(f"         内容: {chunk}")
        
        except Exception as e:
            print(f"   ❌ {method} 方法失败: {str(e)}")


def demo_overlap_analysis():
    """演示重叠分析"""
    print("\n\n🔄 重叠分析")
    print("=" * 60)
    
    from contract_splitter.utils import sliding_window_split
    
    # 测试文本
    test_text = """
    第一条 这是第一个条文的内容，包含了重要的法律规定。第二条 这是第二个条文的内容，与第一条有一定的关联性。第三条 这是第三个条文的内容，进一步细化了相关规定。第四条 这是第四个条文的内容，提供了具体的实施细则。
    """.strip()
    
    print(f"📝 测试文本长度: {len(test_text)} 字符")
    
    # 测试不同的重叠设置
    overlap_settings = [0, 20, 50, 80]
    
    for overlap in overlap_settings:
        print(f"\n🔧 重叠设置: {overlap} 字符")
        
        chunks = sliding_window_split(
            test_text,
            max_tokens=120,
            overlap=overlap,
            by_sentence=True,
            token_counter="character"
        )
        
        print(f"   📊 结果: {len(chunks)} 个chunks")
        
        # 分析重叠内容
        for i, chunk in enumerate(chunks, 1):
            print(f"   Chunk {i} ({len(chunk)}字符): {chunk[:60]}...")
            
            # 检查与前一个chunk的重叠
            if i > 1:
                prev_chunk = chunks[i-2]  # chunks是0-indexed
                
                # 简单的重叠检测 - 查找共同的子字符串
                overlap_found = False
                for start in range(len(prev_chunk)):
                    for end in range(start + 10, len(prev_chunk) + 1):  # 至少10字符的重叠
                        substring = prev_chunk[start:end]
                        if substring in chunk:
                            print(f"      🔄 发现重叠: {substring[:30]}...")
                            overlap_found = True
                            break
                    if overlap_found:
                        break
                
                if not overlap_found:
                    print(f"      ⚠️ 未发现明显重叠")


def main():
    """主函数"""
    print("🚀 高级分块策略示例")
    print("=" * 80)
    print("本示例演示Contract Splitter的高级功能和自定义分块策略")
    
    # 演示各种高级分块功能
    demo_sentence_priority_vs_strict_chunking()
    demo_hierarchical_strategies()
    demo_custom_chunking_parameters()
    demo_token_counting_methods()
    demo_overlap_analysis()
    
    print(f"\n🎉 高级分块策略示例完成")
    print("=" * 80)
    print("💡 高级分块最佳实践:")
    print("1. 优先使用句子完整性分块，避免语义破坏")
    print("2. 根据文档类型选择合适的层次化策略")
    print("3. 调整max_chunk_size和overlap_ratio以获得最佳效果")
    print("4. 对于中文文档，character计数通常比tiktoken更直观")
    print("5. 适当的重叠可以保持上下文连续性")
    print("6. 法律文档建议使用较大的chunk_size以保持条文完整性")


if __name__ == "__main__":
    main()
