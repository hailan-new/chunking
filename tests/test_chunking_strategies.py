#!/usr/bin/env python3
"""
测试不同的chunking策略
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter import ContractSplitter


def test_chunking_strategies():
    """测试不同的chunking策略"""
    print("🚀 测试不同的chunking策略")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    strategies = [
        ("finest_granularity", "同等最细粒度拆分（默认）"),
        ("all_levels", "所有层级拆分"),
        ("parent_only", "仅父级拆分")
    ]
    
    for strategy, description in strategies:
        print(f"\n📋 测试策略: {strategy} - {description}")
        print("-" * 60)
        
        try:
            # 创建splitter
            splitter = ContractSplitter(
                max_tokens=2000,
                overlap=200,
                chunking_strategy=strategy
            )
            
            # 分割文档
            sections = splitter.split(test_file)
            print(f"✅ 分割成功: {len(sections)} 个sections")
            
            # 展平为chunks
            chunks = splitter.flatten(sections)
            print(f"✅ 展平成功: {len(chunks)} 个chunks")
            
            # 分析chunks
            chunk_lengths = [len(chunk) for chunk in chunks]
            avg_length = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
            max_length = max(chunk_lengths) if chunk_lengths else 0
            min_length = min(chunk_lengths) if chunk_lengths else 0
            
            print(f"📊 Chunks统计:")
            print(f"   - 总数: {len(chunks)}")
            print(f"   - 平均长度: {avg_length:.0f} 字符")
            print(f"   - 最大长度: {max_length} 字符")
            print(f"   - 最小长度: {min_length} 字符")
            
            # 检查重复
            unique_chunks = set(chunks)
            if len(unique_chunks) < len(chunks):
                duplicates = len(chunks) - len(unique_chunks)
                print(f"⚠️  发现重复: {duplicates} 个重复chunks")
            else:
                print(f"✅ 无重复内容")
            
            # 显示前3个chunks的预览
            print(f"📝 前3个chunks预览:")
            for i, chunk in enumerate(chunks[:3]):
                preview = chunk[:100].replace('\n', ' ')
                print(f"   Chunk {i+1}: {preview}...")
            
            # 保存结果到文件
            output_file = f"output/strategy_test_{strategy}_chunks.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"策略: {strategy} - {description}\n")
                f.write(f"总chunks数: {len(chunks)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, chunk in enumerate(chunks):
                    f.write(f"【Chunk {i+1:03d}】 (长度: {len(chunk)} 字符)\n")
                    f.write("-" * 40 + "\n")
                    f.write(chunk + "\n")
                    f.write("=" * 80 + "\n\n")
            
            print(f"💾 结果已保存: {output_file}")
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()


def compare_strategies():
    """比较不同策略的结果"""
    print("\n" + "=" * 80)
    print("📊 策略比较总结")
    print("=" * 80)
    
    strategies = ["finest_granularity", "all_levels", "parent_only"]
    
    for strategy in strategies:
        output_file = f"output/strategy_test_{strategy}_chunks.txt"
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    strategy_line = lines[0].strip()
                    chunks_line = lines[1].strip()
                    print(f"📋 {strategy_line}")
                    print(f"   {chunks_line}")
        else:
            print(f"❌ 文件不存在: {output_file}")


def main():
    """主函数"""
    print("🚀 Chunking策略测试")
    print("=" * 80)
    
    test_chunking_strategies()
    compare_strategies()
    
    print("\n" + "=" * 80)
    print("🎯 测试完成")
    print("\n💡 策略说明:")
    print("   - finest_granularity: 只处理叶子节点，避免重复（推荐）")
    print("   - all_levels: 处理所有有内容的节点（可能有重复）")
    print("   - parent_only: 只处理有内容且无子节点的父级")


if __name__ == "__main__":
    main()
