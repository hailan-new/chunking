#!/usr/bin/env python3
"""
测试output/law目录下的WPS和PDF文件拆分效果
并将结果保存到txt文件供人工复核
"""

import os
import glob
import json
import time
from pathlib import Path
from datetime import datetime
from contract_splitter.domain_helpers import split_legal_document

def find_law_documents():
    """查找output/law目录下的WPS和PDF文件"""
    law_dir = "output/law"
    
    # 查找WPS和PDF文件
    wps_files = glob.glob(f"{law_dir}/*.wps")
    pdf_files = glob.glob(f"{law_dir}/*.pdf")
    
    return sorted(wps_files + pdf_files)

def safe_filename(filename):
    """创建安全的文件名"""
    # 移除或替换不安全的字符
    safe_chars = []
    for char in filename:
        if char.isalnum() or char in '.-_':
            safe_chars.append(char)
        elif char in ' /\\':
            safe_chars.append('_')
    
    result = ''.join(safe_chars)
    # 限制长度
    if len(result) > 100:
        result = result[:100]
    
    return result

def save_chunks_to_txt(chunks, output_file, file_path, processing_time):
    """将chunks保存到txt文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        # 写入文件头信息
        f.write("=" * 80 + "\n")
        f.write("法律文档拆分结果 - 人工复核版\n")
        f.write("=" * 80 + "\n")
        f.write(f"原文件: {file_path}\n")
        f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"处理耗时: {processing_time:.2f}秒\n")
        f.write(f"总chunks数: {len(chunks)}\n")
        f.write(f"平均长度: {sum(len(chunk) for chunk in chunks) / len(chunks):.1f}字符\n")
        f.write("=" * 80 + "\n\n")
        
        # 写入每个chunk
        for i, chunk in enumerate(chunks, 1):
            f.write(f"【Chunk {i:03d}】 (长度: {len(chunk)} 字符)\n")
            f.write("-" * 60 + "\n")
            f.write(chunk)
            f.write("\n")
            f.write("=" * 80 + "\n\n")
        
        # 写入统计信息
        f.write("统计信息:\n")
        f.write("-" * 40 + "\n")
        
        # 长度分布
        length_ranges = {
            '0-50': 0, '51-100': 0, '101-200': 0, 
            '201-300': 0, '301-500': 0, '500+': 0
        }
        
        for chunk in chunks:
            length = len(chunk)
            if length <= 50:
                length_ranges['0-50'] += 1
            elif length <= 100:
                length_ranges['51-100'] += 1
            elif length <= 200:
                length_ranges['101-200'] += 1
            elif length <= 300:
                length_ranges['201-300'] += 1
            elif length <= 500:
                length_ranges['301-500'] += 1
            else:
                length_ranges['500+'] += 1
        
        f.write("长度分布:\n")
        for range_name, count in length_ranges.items():
            percentage = (count / len(chunks)) * 100
            f.write(f"  {range_name}字符: {count}个 ({percentage:.1f}%)\n")
        
        # 条文分析（如果是法律文档）
        import re
        article_chunks = []
        for i, chunk in enumerate(chunks, 1):
            if re.search(r'第[一二三四五六七八九十百千万\d]+条', chunk):
                article_chunks.append((i, chunk))
        
        if article_chunks:
            f.write(f"\n条文分析:\n")
            f.write(f"  包含条文的chunks: {len(article_chunks)}个\n")
            f.write(f"  条文覆盖率: {len(article_chunks)/len(chunks)*100:.1f}%\n")
            
            # 列出前10个条文
            f.write(f"  前10个条文:\n")
            for i, (chunk_num, chunk) in enumerate(article_chunks[:10]):
                article_match = re.search(r'第[一二三四五六七八九十百千万\d]+条', chunk)
                if article_match:
                    article_title = article_match.group()
                    f.write(f"    Chunk {chunk_num}: {article_title}\n")

def test_single_file(file_path):
    """测试单个文件"""
    print(f"\n🔍 测试文件: {file_path}")
    print("-" * 60)
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 处理文件
        chunks = split_legal_document(file_path, max_tokens=1500)
        
        # 记录结束时间
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ 处理成功: {len(chunks)} chunks")
        print(f"⏱️  处理时间: {processing_time:.2f}秒")
        
        if chunks:
            avg_length = sum(len(chunk) for chunk in chunks) / len(chunks)
            max_length = max(len(chunk) for chunk in chunks)
            min_length = min(len(chunk) for chunk in chunks)
            
            print(f"📊 统计信息:")
            print(f"   平均长度: {avg_length:.1f} 字符")
            print(f"   最大长度: {max_length} 字符")
            print(f"   最小长度: {min_length} 字符")
            
            # 创建输出文件名
            file_stem = Path(file_path).stem
            safe_name = safe_filename(file_stem)
            output_file = f"output/law_review/{safe_name}_chunks.txt"
            
            # 确保输出目录存在
            os.makedirs("output/law_review", exist_ok=True)
            
            # 保存结果
            save_chunks_to_txt(chunks, output_file, file_path, processing_time)
            print(f"💾 结果已保存: {output_file}")
            
            return True, len(chunks), processing_time
        else:
            print("⚠️  没有生成chunks")
            return False, 0, processing_time
            
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return False, 0, 0

def main():
    """主函数"""
    print("🚀 开始测试output/law目录下的WPS和PDF文件")
    print("=" * 80)
    
    # 查找文件
    files = find_law_documents()
    
    if not files:
        print("❌ 未找到WPS或PDF文件")
        return
    
    print(f"📁 找到 {len(files)} 个文件:")
    for i, file_path in enumerate(files, 1):
        file_type = "WPS" if file_path.endswith('.wps') else "PDF"
        print(f"   {i:2d}. [{file_type}] {os.path.basename(file_path)}")
    
    # 创建输出目录
    os.makedirs("output/law_review", exist_ok=True)
    
    # 处理每个文件
    results = []
    total_start_time = time.time()
    
    for file_path in files:
        success, chunk_count, processing_time = test_single_file(file_path)
        results.append({
            'file': os.path.basename(file_path),
            'success': success,
            'chunks': chunk_count,
            'time': processing_time
        })
    
    total_end_time = time.time()
    total_time = total_end_time - total_start_time
    
    # 生成总结报告
    print("\n" + "=" * 80)
    print("📊 处理结果总结")
    print("=" * 80)
    
    successful_files = [r for r in results if r['success']]
    failed_files = [r for r in results if not r['success']]
    
    print(f"✅ 成功处理: {len(successful_files)}/{len(files)} 个文件")
    print(f"❌ 处理失败: {len(failed_files)} 个文件")
    print(f"⏱️  总处理时间: {total_time:.2f}秒")
    
    if successful_files:
        total_chunks = sum(r['chunks'] for r in successful_files)
        avg_chunks = total_chunks / len(successful_files)
        avg_time = sum(r['time'] for r in successful_files) / len(successful_files)
        
        print(f"📈 成功文件统计:")
        print(f"   总chunks数: {total_chunks}")
        print(f"   平均chunks数: {avg_chunks:.1f}")
        print(f"   平均处理时间: {avg_time:.2f}秒")
    
    if failed_files:
        print(f"\n❌ 失败文件:")
        for result in failed_files:
            print(f"   - {result['file']}")
    
    print(f"\n📁 所有结果已保存到: output/law_review/")
    print(f"💡 请人工复核txt文件中的拆分效果")

if __name__ == "__main__":
    main()
