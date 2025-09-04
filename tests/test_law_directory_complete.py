#!/usr/bin/env python3
"""
对output/law目录进行完全测试
为每个文件生成包含所有chunks的txt文件
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.domain_helpers import split_legal_document


def test_law_directory_complete():
    """对output/law目录进行完全测试"""
    
    print("🏛️ 法律文档目录完全测试")
    print("=" * 80)
    
    law_dir = Path("output/law")
    output_dir = Path("output/law_chunks_complete")
    
    # 创建输出目录
    output_dir.mkdir(exist_ok=True)
    
    if not law_dir.exists():
        print(f"❌ 目录不存在: {law_dir}")
        return
    
    # 获取所有支持的文件
    supported_extensions = ['.docx', '.doc', '.pdf', '.wps']
    law_files = []
    
    for ext in supported_extensions:
        law_files.extend(law_dir.glob(f"*{ext}"))
    
    if not law_files:
        print(f"❌ 在 {law_dir} 中没有找到支持的文件")
        return
    
    print(f"📁 找到 {len(law_files)} 个法律文档文件")
    print(f"📤 输出目录: {output_dir}")
    print()
    
    results = {}
    total_chunks = 0
    
    for i, file_path in enumerate(law_files, 1):
        file_name = file_path.name
        print(f"[{i}/{len(law_files)}] 📄 处理: {file_name}")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            # 使用法律文档专用切分器
            chunks = split_legal_document(str(file_path), max_tokens=1500)
            
            # 保存chunks到文件
            output_file = save_law_chunks_to_file(file_name, chunks, output_dir, str(file_path))
            
            processing_time = time.time() - start_time
            
            results[file_name] = {
                'success': True,
                'chunks_count': len(chunks),
                'output_file': output_file,
                'processing_time': processing_time,
                'file_size': file_path.stat().st_size
            }
            
            total_chunks += len(chunks)
            
            print(f"✅ 成功: {len(chunks)} chunks")
            print(f"⏱️  耗时: {processing_time:.2f}s")
            print(f"💾 保存到: {output_file}")
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            results[file_name] = {
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
            
            print(f"❌ 失败: {e}")
            print(f"⏱️  耗时: {processing_time:.2f}s")
        
        print()
    
    # 生成总结报告
    generate_law_test_report(results, total_chunks, output_dir)
    
    return results


def save_law_chunks_to_file(file_name: str, chunks: list, output_dir: Path, original_path: str) -> str:
    """保存法律文档chunks到文件"""
    
    # 生成输出文件名
    base_name = Path(file_name).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{base_name}_法律条文切分_{timestamp}.txt"
    
    # 写入chunks
    with open(output_file, 'w', encoding='utf-8') as f:
        # 文件头信息
        f.write("🏛️ 法律文档智能切分结果\n")
        f.write("=" * 80 + "\n")
        f.write(f"📄 原文件: {file_name}\n")
        f.write(f"📂 文件路径: {original_path}\n")
        f.write(f"⏰ 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"📊 总chunks数: {len(chunks)}\n")
        f.write(f"🔧 切分方式: 层次化法律条文切分\n")
        f.write("=" * 80 + "\n\n")
        
        # 写入每个chunk
        for i, chunk in enumerate(chunks, 1):
            f.write(f"📋 Chunk {i:03d}\n")
            f.write("-" * 40 + "\n")
            f.write(f"📏 长度: {len(chunk)} 字符\n")
            f.write("-" * 40 + "\n")
            f.write(chunk)
            f.write("\n\n" + "=" * 80 + "\n\n")
        
        # 文件尾信息
        f.write("📊 切分统计信息\n")
        f.write("-" * 40 + "\n")
        f.write(f"总chunks数: {len(chunks)}\n")
        f.write(f"平均长度: {sum(len(chunk) for chunk in chunks) / len(chunks):.1f} 字符\n")
        f.write(f"最长chunk: {max(len(chunk) for chunk in chunks)} 字符\n")
        f.write(f"最短chunk: {min(len(chunk) for chunk in chunks)} 字符\n")
        
        # 分析chunk结构
        analyze_chunk_structure_in_file(chunks, f)
    
    return str(output_file)


def analyze_chunk_structure_in_file(chunks: list, file_handle):
    """在文件中分析chunk结构"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from contract_splitter.legal_structure_detector import get_legal_detector, LegalStructureLevel

    file_handle.write("\n📈 结构分析\n")
    file_handle.write("-" * 40 + "\n")

    # 统计不同类型的chunk
    structure_stats = {
        '章节': 0,    # 第X章
        '条文': 0,    # 第X条
        '款项': 0,    # 第X款
        '序号': 0,    # (一)、(二)
        '普通内容': 0
    }

    # 使用统一的结构检测器
    detector = get_legal_detector("legal")
    
    for chunk in chunks:
        chunk_type = '普通内容'

        # 使用统一的结构检测器判断类型
        if detector.is_legal_heading(chunk):
            level = detector.get_heading_level(chunk)
            if level in [LegalStructureLevel.CHAPTER.value, LegalStructureLevel.BOOK.value, LegalStructureLevel.PART.value]:
                chunk_type = '章节'
            elif level == LegalStructureLevel.ARTICLE.value:
                chunk_type = '条文'
            elif level in [LegalStructureLevel.CLAUSE.value, LegalStructureLevel.ITEM.value]:
                chunk_type = '款项'
            elif level >= LegalStructureLevel.ENUMERATION.value:
                chunk_type = '序号'

        structure_stats[chunk_type] += 1
    
    # 写入统计结果
    for type_name, count in structure_stats.items():
        if count > 0:
            percentage = (count / len(chunks)) * 100
            file_handle.write(f"{type_name}: {count} ({percentage:.1f}%)\n")


def generate_law_test_report(results: dict, total_chunks: int, output_dir: Path):
    """生成法律文档测试报告"""
    
    print("=" * 80)
    print("📊 法律文档测试总结报告")
    print("=" * 80)
    
    total_files = len(results)
    successful_files = sum(1 for r in results.values() if r['success'])
    failed_files = total_files - successful_files
    
    print(f"📁 总文件数: {total_files}")
    print(f"✅ 成功处理: {successful_files}")
    print(f"❌ 处理失败: {failed_files}")
    print(f"📈 成功率: {successful_files/total_files*100:.1f}%")
    print(f"📊 总chunks数: {total_chunks}")
    
    if successful_files > 0:
        avg_chunks = total_chunks / successful_files
        print(f"📊 平均chunks数: {avg_chunks:.1f}")
        
        # 计算总处理时间
        total_time = sum(r.get('processing_time', 0) for r in results.values())
        print(f"⏱️  总处理时间: {total_time:.2f}s")
        print(f"⚡ 平均处理时间: {total_time/total_files:.2f}s/文件")
    
    print(f"\n📂 输出目录: {output_dir}")
    
    # 详细结果
    print(f"\n📋 详细处理结果:")
    print("-" * 60)
    
    # 按文件格式分组显示
    by_format = {}
    for file_name, result in results.items():
        ext = Path(file_name).suffix.lower()
        if ext not in by_format:
            by_format[ext] = []
        by_format[ext].append((file_name, result))
    
    for ext, files in by_format.items():
        print(f"\n📄 {ext.upper()} 文件:")
        for file_name, result in files:
            if result['success']:
                chunks_count = result['chunks_count']
                time_taken = result['processing_time']
                print(f"  ✅ {file_name}: {chunks_count} chunks ({time_taken:.2f}s)")
            else:
                error = result['error']
                print(f"  ❌ {file_name}: {error}")
    
    # 保存报告到文件
    report_file = output_dir / f"法律文档测试报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    save_report_to_file(results, total_chunks, report_file)
    print(f"\n📄 详细报告已保存到: {report_file}")


def save_report_to_file(results: dict, total_chunks: int, report_file: Path):
    """保存报告到文件"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("🏛️ 法律文档目录完全测试报告\n")
        f.write("=" * 80 + "\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试目录: output/law\n")
        f.write("=" * 80 + "\n\n")
        
        # 统计信息
        total_files = len(results)
        successful_files = sum(1 for r in results.values() if r['success'])
        
        f.write("📊 统计信息\n")
        f.write("-" * 40 + "\n")
        f.write(f"总文件数: {total_files}\n")
        f.write(f"成功处理: {successful_files}\n")
        f.write(f"处理失败: {total_files - successful_files}\n")
        f.write(f"成功率: {successful_files/total_files*100:.1f}%\n")
        f.write(f"总chunks数: {total_chunks}\n")
        
        if successful_files > 0:
            avg_chunks = total_chunks / successful_files
            f.write(f"平均chunks数: {avg_chunks:.1f}\n")
        
        f.write("\n📋 详细结果\n")
        f.write("-" * 40 + "\n")
        
        for file_name, result in results.items():
            f.write(f"\n文件: {file_name}\n")
            if result['success']:
                f.write(f"  状态: ✅ 成功\n")
                f.write(f"  Chunks数: {result['chunks_count']}\n")
                f.write(f"  处理时间: {result['processing_time']:.2f}s\n")
                f.write(f"  输出文件: {result['output_file']}\n")
            else:
                f.write(f"  状态: ❌ 失败\n")
                f.write(f"  错误信息: {result['error']}\n")
                f.write(f"  处理时间: {result['processing_time']:.2f}s\n")


if __name__ == "__main__":
    test_law_directory_complete()
