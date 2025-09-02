#!/usr/bin/env python3
"""
快速测试当前chunking结果
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter import ContractSplitter


def main():
    """主函数"""
    print("🚀 快速测试当前chunking结果")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    try:
        # 创建splitter
        splitter = ContractSplitter(
            max_tokens=2000,
            overlap=200,
            chunking_strategy="finest_granularity"
        )
        
        # 分割文档
        sections = splitter.split(test_file)
        print(f"✅ 分割成功: {len(sections)} 个sections")
        
        # 展平为chunks
        chunks = splitter.flatten(sections)
        print(f"✅ 展平成功: {len(chunks)} 个chunks")
        
        # 显示前5个chunks
        print(f"\n📝 前5个chunks:")
        for i, chunk in enumerate(chunks[:5]):
            print(f"Chunk {i+1} (长度: {len(chunk)}): {chunk[:80]}...")
        
        # 检查重复
        unique_chunks = set(chunks)
        if len(unique_chunks) < len(chunks):
            duplicates = len(chunks) - len(unique_chunks)
            print(f"\n⚠️  发现重复: {duplicates} 个重复chunks")
        else:
            print(f"\n✅ 无重复内容")
        
        # 保存到新文件
        output_file = "output/quick_test_chunks.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"快速测试结果\n")
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


if __name__ == "__main__":
    main()
