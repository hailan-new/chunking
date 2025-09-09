#!/usr/bin/env python3
"""
简单粗暴Chunking方法使用示例
演示如何使用SimpleChunker进行文档分割
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def example_simple_file_chunking():
    """示例：文件chunking"""
    print("📄 文件Chunking示例")
    print("=" * 50)
    
    from contract_splitter import simple_chunk_file
    
    # 假设有一个测试文件
    test_file = "output/law/附件1.期货公司互联网营销管理暂行规定.pdf"
    
    if os.path.exists(test_file):
        print(f"处理文件: {os.path.basename(test_file)}")
        
        # 使用默认配置
        chunks = simple_chunk_file(test_file)
        
        print(f"生成 {len(chunks)} 个chunks")
        
        # 显示前3个chunks
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i+1}:")
            print(f"  长度: {chunk['length']} 字符")
            print(f"  位置: {chunk['start_pos']}-{chunk['end_pos']}")
            print(f"  内容: {chunk['content'][:100]}...")
    else:
        print(f"测试文件不存在: {test_file}")


def example_simple_text_chunking():
    """示例：文本chunking"""
    print("\n📝 文本Chunking示例")
    print("=" * 50)
    
    from contract_splitter import simple_chunk_text
    
    # 测试文本
    text = """
    第一条 为了规范期货公司互联网营销活动，保障期货交易者合法权益，根据相关法律法规制定本规定。
    
    第二条 本规定适用于期货公司通过互联网开展的营销活动。期货公司应当建立健全互联网营销管理制度。
    
    第三条 期货公司开展互联网营销应当遵循诚实信用、公平竞争的原则，不得损害投资者合法权益。
    
    第四条 期货公司应当对互联网营销内容进行审核，确保营销内容真实、准确、完整。
    
    第五条 期货公司不得通过互联网进行虚假宣传或误导性营销。
    """
    
    print(f"原始文本长度: {len(text)} 字符")
    
    # 使用不同配置进行chunking
    configs = [
        {"max_chunk_size": 100, "overlap_ratio": 0.1, "name": "小chunks"},
        {"max_chunk_size": 200, "overlap_ratio": 0.15, "name": "中chunks"},
        {"max_chunk_size": 300, "overlap_ratio": 0.2, "name": "大chunks"},
    ]
    
    for config in configs:
        print(f"\n🔧 {config['name']} (max_size={config['max_chunk_size']}, overlap={config['overlap_ratio']})")
        
        chunks = simple_chunk_text(
            text,
            max_chunk_size=config['max_chunk_size'],
            overlap_ratio=config['overlap_ratio']
        )
        
        print(f"生成 {len(chunks)} 个chunks")
        
        for i, chunk in enumerate(chunks):
            content = chunk['content'].strip()
            print(f"  Chunk {i+1} ({len(content)}字符): {content[:50]}...")


def example_class_usage():
    """示例：使用SimpleChunker类"""
    print("\n🔧 SimpleChunker类使用示例")
    print("=" * 50)
    
    from contract_splitter import SimpleChunker
    
    # 创建chunker实例
    chunker = SimpleChunker(max_chunk_size=150, overlap_ratio=0.15)
    
    # 测试文本
    text = """
    这是一个测试文档。文档包含多个段落和句子！
    
    每个段落都有不同的内容？我们需要测试chunking算法的效果。
    
    算法应该能够在合适的位置进行分割。保持文本的完整性和可读性。
    
    最后一段用来测试结束逻辑。
    """
    
    print(f"Chunker配置: max_size={chunker.max_chunk_size}, overlap_ratio={chunker.overlap_ratio}")
    
    # 进行chunking
    chunks = chunker.chunk_text(text)
    
    print(f"生成 {len(chunks)} 个chunks")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"  ID: {chunk['chunk_id']}")
        print(f"  长度: {chunk['length']} 字符")
        print(f"  位置: {chunk['start_pos']}-{chunk['end_pos']}")
        print(f"  内容: {chunk['content']}")


def example_different_file_types():
    """示例：处理不同类型的文件"""
    print("\n📁 不同文件类型处理示例")
    print("=" * 50)
    
    from contract_splitter import SimpleChunker
    
    chunker = SimpleChunker(max_chunk_size=1000, overlap_ratio=0.1)
    
    # 查找不同类型的测试文件
    test_dir = Path("output/law")
    if test_dir.exists():
        file_types = {
            '.pdf': 'PDF文件',
            '.docx': 'Word文档',
            '.doc': 'Word文档(旧版)',
            '.wps': 'WPS文档',
            '.txt': '文本文件'
        }
        
        for file_type, description in file_types.items():
            files = list(test_dir.glob(f"*{file_type}"))
            if files:
                test_file = files[0]  # 取第一个文件
                print(f"\n📄 处理{description}: {test_file.name}")
                
                try:
                    chunks = chunker.chunk_file(str(test_file))
                    
                    if chunks:
                        total_length = sum(chunk['length'] for chunk in chunks)
                        avg_length = total_length / len(chunks)
                        
                        print(f"  ✅ 成功: {len(chunks)}个chunks, 总长度{total_length}字符")
                        print(f"  📏 平均长度: {avg_length:.0f}字符")
                        
                        # 显示第一个chunk的预览
                        if chunks:
                            preview = chunks[0]['content'][:100] + "..." if len(chunks[0]['content']) > 100 else chunks[0]['content']
                            print(f"  📄 预览: {preview}")
                    else:
                        print(f"  ❌ 未生成chunks")
                        
                except Exception as e:
                    print(f"  ❌ 处理失败: {e}")
            else:
                print(f"\n📄 {description}: 未找到测试文件")
    else:
        print("测试目录不存在")


def example_quality_analysis():
    """示例：chunk质量分析"""
    print("\n📊 Chunk质量分析示例")
    print("=" * 50)
    
    from contract_splitter import simple_chunk_text
    
    # 测试文本（包含不同的句子结尾）
    text = """
    第一条 这是第一条规定。内容比较简单！
    
    第二条 这是第二条规定？内容稍微复杂一些。包含了更多的细节说明。
    
    第三条 这是第三条规定
    内容分为多行
    每行都有不同的信息
    
    第四条 最后一条规定。结束了整个文档。
    """
    
    chunks = simple_chunk_text(text, max_chunk_size=100, overlap_ratio=0.1)
    
    print(f"生成 {len(chunks)} 个chunks")
    
    # 分析chunk质量
    sentence_endings = ['\n', '。', '！', '？', '.', '!', '?']
    
    print(f"\n📈 质量分析:")
    
    for i, chunk in enumerate(chunks):
        content = chunk['content']
        
        # 检查是否以句子结尾
        ends_properly = content and content[-1] in sentence_endings
        
        # 检查长度
        length = len(content)
        
        print(f"  Chunk {i+1}:")
        print(f"    长度: {length} 字符")
        print(f"    句子结尾: {'✅' if ends_properly else '❌'}")
        print(f"    内容: {content.strip()}")


def main():
    """主函数"""
    print("🚀 简单粗暴Chunking方法使用示例")
    print("=" * 80)
    
    # 运行各种示例
    example_simple_file_chunking()
    example_simple_text_chunking()
    example_class_usage()
    example_different_file_types()
    example_quality_analysis()
    
    print("\n🎯 总结")
    print("=" * 80)
    print("简单粗暴的chunking方法特点:")
    print("1. ✅ 简单易用 - 只需指定max_chunk_size和overlap_ratio")
    print("2. ✅ 智能分割 - 在句子边界进行分割，保持文本完整性")
    print("3. ✅ 支持重叠 - 可配置的重叠比例，提高上下文连续性")
    print("4. ✅ 多格式支持 - 支持PDF、DOCX、WPS、RTF、TXT等格式")
    print("5. ✅ 便捷接口 - 提供函数式和类式两种使用方式")
    
    print("\n💡 使用建议:")
    print("- 对于一般文档，推荐max_chunk_size=1500, overlap_ratio=0.15")
    print("- 对于法律文档，可以适当增大chunk_size到2000")
    print("- 如果需要更好的上下文连续性，可以增加overlap_ratio到0.2")


if __name__ == "__main__":
    main()
