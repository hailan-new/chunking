#!/usr/bin/env python3
"""
测试层次化法律条文切分功能
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.domain_helpers import split_legal_document


def test_hierarchical_legal_splitting():
    """测试层次化法律条文切分"""
    
    print("🔍 层次化法律条文切分测试")
    print("=" * 80)
    
    # 测试文件列表
    test_files = [
        'output/law/9147de404f6d4df986b0cb41acd47aac.wps',
        'output/law/证券公司监督管理条例(2014年修订).docx',
        'output/law/附件1.期货公司互联网营销管理暂行规定.pdf'
    ]
    
    results = {}
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"⚠️  文件不存在: {test_file}")
            continue
            
        file_name = os.path.basename(test_file)
        print(f"\n📄 测试文件: {file_name}")
        print("-" * 60)
        
        try:
            # 使用层次化切分
            chunks = split_legal_document(test_file, max_tokens=1500)
            
            results[file_name] = {
                'success': True,
                'chunks_count': len(chunks),
                'chunks': chunks
            }
            
            print(f"✅ 处理成功: {len(chunks)} chunks")
            
            # 分析chunk结构
            analyze_chunk_structure(chunks, file_name)
            
        except Exception as e:
            results[file_name] = {
                'success': False,
                'error': str(e)
            }
            print(f"❌ 处理失败: {e}")
    
    # 生成总结报告
    generate_summary_report(results)
    
    return results


def analyze_chunk_structure(chunks, file_name):
    """分析chunk结构"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from contract_splitter.legal_structure_detector import get_legal_detector, LegalStructureLevel

    print(f"\n📊 {file_name} 结构分析:")

    # 统计不同层次的chunk数量
    structure_stats = {
        'chapter': 0,    # 章节
        'article': 0,    # 条文
        'item': 0,       # 序号
        'content': 0     # 普通内容
    }

    # 使用统一的结构检测器
    detector = get_legal_detector("legal")
    
    for chunk in chunks:
        chunk_type = 'content'

        # 使用统一的结构检测器判断类型
        if detector.is_legal_heading(chunk):
            level = detector.get_heading_level(chunk)
            if level == LegalStructureLevel.CHAPTER.value or level == LegalStructureLevel.BOOK.value:
                chunk_type = 'chapter'
            elif level == LegalStructureLevel.ARTICLE.value:
                chunk_type = 'article'
            elif level >= LegalStructureLevel.ENUMERATION.value:
                chunk_type = 'item'

        structure_stats[chunk_type] += 1
    
    # 显示统计结果
    for type_name, count in structure_stats.items():
        if count > 0:
            print(f"  {type_name}: {count}")
    
    # 显示前3个chunk的预览
    print(f"\n📝 前3个chunks预览:")
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n  Chunk {i} (长度: {len(chunk)}):")
        print("  " + "-" * 38)
        # 显示前200个字符
        preview = chunk[:200].replace('\n', ' ')
        if len(chunk) > 200:
            preview += "..."
        print(f"  {preview}")


def generate_summary_report(results):
    """生成总结报告"""
    print("\n" + "=" * 80)
    print("📊 层次化切分测试总结")
    print("=" * 80)
    
    total_files = len(results)
    successful_files = sum(1 for r in results.values() if r['success'])
    total_chunks = sum(r.get('chunks_count', 0) for r in results.values() if r['success'])
    
    print(f"总文件数: {total_files}")
    print(f"成功处理: {successful_files}")
    print(f"成功率: {successful_files/total_files*100:.1f}%")
    print(f"总chunks数: {total_chunks}")
    
    if successful_files > 0:
        avg_chunks = total_chunks / successful_files
        print(f"平均chunks数: {avg_chunks:.1f}")
    
    print("\n📋 详细结果:")
    for file_name, result in results.items():
        if result['success']:
            print(f"  ✅ {file_name}: {result['chunks_count']} chunks")
        else:
            print(f"  ❌ {file_name}: {result['error']}")


def compare_with_previous_results():
    """与之前的结果对比"""
    print("\n🔄 与之前结果对比:")
    print("-" * 40)
    
    # 这里可以添加与之前结果的对比逻辑
    # 比如从保存的结果文件中读取之前的数据进行对比
    
    previous_results = {
        '9147de404f6d4df986b0cb41acd47aac.wps': 4,  # 之前的结果
        '证券公司监督管理条例(2014年修订).docx': 22,
    }
    
    current_results = test_hierarchical_legal_splitting()
    
    for file_name in previous_results:
        if file_name in current_results and current_results[file_name]['success']:
            prev_count = previous_results[file_name]
            curr_count = current_results[file_name]['chunks_count']
            change = curr_count - prev_count
            change_pct = (change / prev_count) * 100 if prev_count > 0 else 0
            
            print(f"  {file_name}:")
            print(f"    之前: {prev_count} chunks")
            print(f"    现在: {curr_count} chunks")
            print(f"    变化: {change:+d} ({change_pct:+.1f}%)")


if __name__ == "__main__":
    test_hierarchical_legal_splitting()
