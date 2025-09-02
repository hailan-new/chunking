#!/usr/bin/env python3
"""
批量测试output目录下的所有文档文件
"""

import os
import sys
import glob
import time
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.docx_splitter import DocxSplitter


def get_all_document_files():
    """获取output目录下的所有文档文件"""
    output_dir = "output"
    
    # 支持的文件扩展名
    extensions = ['*.doc', '*.docx']
    
    files = []
    for ext in extensions:
        pattern = os.path.join(output_dir, ext)
        files.extend(glob.glob(pattern))
    
    # 过滤掉一些测试文件
    filtered_files = []
    for file in files:
        filename = os.path.basename(file)
        # 跳过一些明显的测试文件
        if not filename.startswith('test') and not filename.startswith('sample'):
            filtered_files.append(file)
    
    return sorted(filtered_files)


def test_single_file(file_path, file_index, total_files):
    """测试单个文件"""
    print(f"\n{'='*80}")
    print(f"📄 测试文件 {file_index}/{total_files}: {os.path.basename(file_path)}")
    print(f"{'='*80}")
    
    try:
        # 创建DocxSplitter
        splitter = DocxSplitter(max_tokens=2000, overlap=200)
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行分割
        sections = splitter.split(file_path)
        
        # 记录分割时间
        split_time = time.time() - start_time
        
        # 执行flatten
        flatten_start = time.time()
        chunks = splitter.flatten(sections)
        flatten_time = time.time() - flatten_start
        
        total_time = time.time() - start_time
        
        # 分析结果
        print(f"✅ 处理成功!")
        print(f"   📊 统计信息:")
        print(f"      - Sections数量: {len(sections)}")
        print(f"      - Chunks数量: {len(chunks)}")
        print(f"      - 处理时间: {total_time:.2f}s (分割: {split_time:.2f}s, 展平: {flatten_time:.2f}s)")
        
        if chunks:
            chunk_lengths = [len(chunk) for chunk in chunks]
            print(f"      - 平均chunk长度: {sum(chunk_lengths) / len(chunk_lengths):.0f} 字符")
            print(f"      - 最大chunk长度: {max(chunk_lengths)} 字符")
            print(f"      - 最小chunk长度: {min(chunk_lengths)} 字符")
        
        # 检查关键内容
        total_content = " ".join(chunks)
        
        # 检查是否包含常见的重要内容标记
        important_markers = [
            "一、", "二、", "三、", "四、", "五、",
            "第一", "第二", "第三", "第四", "第五",
            "合同", "协议", "条款", "甲方", "乙方",
            "投资", "管理", "风险", "收益"
        ]
        
        found_markers = [marker for marker in important_markers if marker in total_content]
        print(f"      - 包含重要标记: {len(found_markers)}/20 ({', '.join(found_markers[:5])}...)")
        
        # 检查是否有重复内容（简单检查）
        if len(chunks) > 1:
            # 检查相邻chunks是否有大量重复
            max_overlap = 0
            for i in range(len(chunks) - 1):
                chunk1 = chunks[i]
                chunk2 = chunks[i + 1]
                
                # 简单的重复检测：检查chunk1的后100字符是否在chunk2的前200字符中
                if len(chunk1) > 100 and len(chunk2) > 100:
                    tail = chunk1[-100:]
                    head = chunk2[:200]
                    if tail in head:
                        overlap_ratio = len(tail) / len(chunk1)
                        max_overlap = max(max_overlap, overlap_ratio)
            
            if max_overlap > 0.1:  # 如果重复超过10%
                print(f"      ⚠️  检测到可能的重复内容: {max_overlap:.1%}")
            else:
                print(f"      ✅ 无明显重复内容")
        
        # 显示第一个chunk的预览
        if chunks:
            preview = chunks[0][:200].replace('\n', ' ')
            print(f"   📝 第一个chunk预览: {preview}...")
        
        return {
            'file': file_path,
            'success': True,
            'sections': len(sections),
            'chunks': len(chunks),
            'total_time': total_time,
            'avg_chunk_length': sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0,
            'max_chunk_length': max(len(chunk) for chunk in chunks) if chunks else 0,
            'min_chunk_length': min(len(chunk) for chunk in chunks) if chunks else 0,
            'has_content': len(total_content) > 100,
            'important_markers': len(found_markers),
            'max_overlap': max_overlap if len(chunks) > 1 else 0
        }
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        
        return {
            'file': file_path,
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


def main():
    """主函数"""
    print("🚀 批量测试output目录下的所有文档文件")
    print("=" * 80)
    
    # 获取所有文档文件
    files = get_all_document_files()
    
    if not files:
        print("❌ 未找到任何文档文件")
        return
    
    print(f"📁 找到 {len(files)} 个文档文件:")
    for i, file in enumerate(files, 1):
        print(f"   {i}. {os.path.basename(file)}")
    
    # 测试每个文件
    results = []
    successful_tests = 0
    failed_tests = 0
    
    for i, file in enumerate(files, 1):
        result = test_single_file(file, i, len(files))
        results.append(result)
        
        if result['success']:
            successful_tests += 1
        else:
            failed_tests += 1
        
        # 添加分隔符
        if i < len(files):
            print("\n" + "-" * 40)
    
    # 生成总结报告
    print(f"\n{'='*80}")
    print(f"📊 批量测试总结报告")
    print(f"{'='*80}")
    
    print(f"📈 总体统计:")
    print(f"   - 总文件数: {len(files)}")
    print(f"   - 成功处理: {successful_tests}")
    print(f"   - 处理失败: {failed_tests}")
    print(f"   - 成功率: {successful_tests/len(files)*100:.1f}%")
    
    if successful_tests > 0:
        successful_results = [r for r in results if r['success']]
        
        avg_sections = sum(r['sections'] for r in successful_results) / len(successful_results)
        avg_chunks = sum(r['chunks'] for r in successful_results) / len(successful_results)
        avg_time = sum(r['total_time'] for r in successful_results) / len(successful_results)
        avg_chunk_length = sum(r['avg_chunk_length'] for r in successful_results) / len(successful_results)
        
        print(f"\n📊 成功处理文件的平均指标:")
        print(f"   - 平均sections数: {avg_sections:.1f}")
        print(f"   - 平均chunks数: {avg_chunks:.1f}")
        print(f"   - 平均处理时间: {avg_time:.2f}s")
        print(f"   - 平均chunk长度: {avg_chunk_length:.0f} 字符")
        
        # 检查问题文件
        problem_files = [r for r in successful_results if r['max_overlap'] > 0.1 or r['chunks'] == 0 or not r['has_content']]
        if problem_files:
            print(f"\n⚠️  需要关注的文件 ({len(problem_files)}个):")
            for r in problem_files:
                issues = []
                if r['max_overlap'] > 0.1:
                    issues.append(f"重复内容{r['max_overlap']:.1%}")
                if r['chunks'] == 0:
                    issues.append("无chunks")
                if not r['has_content']:
                    issues.append("内容过少")
                
                print(f"   - {os.path.basename(r['file'])}: {', '.join(issues)}")
    
    if failed_tests > 0:
        failed_results = [r for r in results if not r['success']]
        print(f"\n❌ 处理失败的文件 ({failed_tests}个):")
        for r in failed_results:
            print(f"   - {os.path.basename(r['file'])}: {r['error_type']} - {r['error'][:100]}...")
    
    print(f"\n🎯 测试完成! 请人工检查上述结果。")
    print(f"💡 建议重点关注:")
    print(f"   1. 处理失败的文件")
    print(f"   2. 有重复内容的文件")
    print(f"   3. chunks数量异常的文件")
    print(f"   4. 处理时间过长的文件")


if __name__ == "__main__":
    main()
