#!/usr/bin/env python3
"""
综合Chunk测试脚本 - 支持output目录下的.doc/.docx/.pdf文件
"""
 
import sys
import os
import json
import glob
from pathlib import Path
from typing import List, Dict, Any
 
# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
 
from contract_splitter import ContractSplitter, split_document, flatten_sections
from contract_splitter.domain_helpers import split_legal_document, split_contract, split_regulation
from contract_splitter.utils import (
    count_tokens, split_chinese_sentences, sliding_window_split, clean_text
)
 
 
def find_document_files() -> List[str]:
    """查找output目录下的所有支持格式的文档"""
    supported_extensions = ['*.doc', '*.docx', '*.pdf', '*.wps']
    document_files = []

    for ext in supported_extensions:
        files = glob.glob(f"output/{ext}")
        document_files.extend(files)
        # 也搜索子目录
        files = glob.glob(f"output/*/{ext}")
        document_files.extend(files)

    return sorted(document_files)


def find_wps_files() -> List[str]:
    """专门查找WPS文件"""
    wps_files = []

    # 搜索output目录及其子目录下的WPS文件
    wps_files.extend(glob.glob("output/*.wps"))
    wps_files.extend(glob.glob("output/*/*.wps"))
    wps_files.extend(glob.glob("output/*/*/*.wps"))

    return sorted(wps_files)


def is_legal_document(file_path: str) -> bool:
    """检测是否为法律文档"""
    file_path_lower = file_path.lower()

    # 检查路径中是否包含法律相关关键词
    legal_keywords = ['law', '法律', '法规', '条例', '办法', '规定', '管理', '监督', '证券', '银行', '金融']

    # 检查文件路径
    if '/law/' in file_path_lower or '\\law\\' in file_path_lower:
        return True

    # 检查文件名
    file_name = Path(file_path).stem.lower()
    for keyword in legal_keywords:
        if keyword in file_name:
            return True

    return False
 
 
def test_file_chunking(file_path: str) -> Dict[str, Any]:
    """对单个文件进行chunking测试"""
    print(f"\n{'='*60}")
    print(f"测试文件: {file_path}")
    print(f"{'='*60}")
    
    result = {
        "file_path": file_path,
        "file_size": os.path.getsize(file_path),
        "file_extension": Path(file_path).suffix.lower(),
        "test_results": {}
    }
    
    try:
        # 测试不同的chunking策略
        strategies = [
            {"name": "small_chunks", "max_tokens": 500, "overlap": 50},
            {"name": "medium_chunks", "max_tokens": 1000, "overlap": 100},
            {"name": "large_chunks", "max_tokens": 2000, "overlap": 200}
        ]
        
        for strategy in strategies:
            print(f"\n--- 策略: {strategy['name']} (max_tokens={strategy['max_tokens']}, overlap={strategy['overlap']}) ---")
            
            strategy_result = {
                "max_tokens": strategy["max_tokens"],
                "overlap": strategy["overlap"],
                "hierarchical_sections": None,
                "flattened_chunks": None,
                "processing_time": None
            }
            
            import time
            start_time = time.time()
            
            try:
                # 智能选择处理方法
                if is_legal_document(file_path):
                    print(f"  📚 检测到法律文档，使用专用切分器")
                    # 使用法律文档专用切分器
                    chunks = split_legal_document(
                        file_path,
                        max_tokens=strategy["max_tokens"]
                    )

                    # 模拟sections结构以保持兼容性
                    sections = [{"heading": f"法律条文 {i+1}", "content": chunk, "subsections": []}
                              for i, chunk in enumerate(chunks)]
                    flattened_chunks = chunks
                else:
                    print(f"  📄 使用通用切分器")
                    # 使用ContractSplitter进行层次化分割
                    splitter = ContractSplitter(
                        max_tokens=strategy["max_tokens"],
                        overlap=strategy["overlap"],
                        split_by_sentence=True,
                        token_counter="character"
                    )

                    # 获取层次化结构
                    sections = splitter.split(file_path)
                    # 展平为chunks
                    flattened_chunks = splitter.flatten(sections)

                strategy_result["hierarchical_sections"] = {
                    "num_sections": len(sections),
                    "sections_preview": []
                }
                
                # 展示前几个sections的结构
                for i, section in enumerate(sections[:3]):
                    section_info = {
                        "section_id": i,
                        "heading": section.get("heading", "无标题"),
                        "level": section.get("level", 0),
                        "content_length": len(section.get("content", "")),
                        "content_preview": section.get("content", "")[:100] + "...",
                        "num_subsections": len(section.get("subsections", []))
                    }
                    strategy_result["hierarchical_sections"]["sections_preview"].append(section_info)
                
                print(f"✓ 层次化分割成功: {len(sections)} 个sections")

                strategy_result["flattened_chunks"] = {
                    "num_chunks": len(flattened_chunks),
                    "chunks_preview": []
                }
                
                # 展示前几个chunks
                for i, chunk in enumerate(flattened_chunks[:3]):
                    chunk_info = {
                        "chunk_id": i,
                        "length": len(chunk),
                        "preview": chunk[:150] + "..." if len(chunk) > 150 else chunk
                    }
                    strategy_result["flattened_chunks"]["chunks_preview"].append(chunk_info)
                
                print(f"✓ 展平分割成功: {len(flattened_chunks)} 个chunks")
                
                # 分析chunks质量
                if flattened_chunks:
                    avg_chunk_length = sum(len(chunk) for chunk in flattened_chunks) / len(flattened_chunks)
                    max_chunk_length = max(len(chunk) for chunk in flattened_chunks)
                    min_chunk_length = min(len(chunk) for chunk in flattened_chunks)
                    
                    strategy_result["chunk_analysis"] = {
                        "avg_chunk_length": round(avg_chunk_length, 2),
                        "max_chunk_length": max_chunk_length,
                        "min_chunk_length": min_chunk_length,
                        "chunks_within_limit": sum(1 for chunk in flattened_chunks if len(chunk) <= strategy["max_tokens"])
                    }
                    
                    print(f"  平均chunk长度: {avg_chunk_length:.0f} 字符")
                    print(f"  最大chunk长度: {max_chunk_length} 字符")
                    print(f"  最小chunk长度: {min_chunk_length} 字符")
                    print(f"  符合长度限制的chunks: {strategy_result['chunk_analysis']['chunks_within_limit']}/{len(flattened_chunks)}")
                
            except Exception as e:
                print(f"✗ 处理失败: {e}")
                strategy_result["error"] = str(e)
            
            finally:
                strategy_result["processing_time"] = round(time.time() - start_time, 2)
                print(f"  处理时间: {strategy_result['processing_time']}s")
            
            result["test_results"][strategy["name"]] = strategy_result
        
    except Exception as e:
        print(f"✗ 文件处理失败: {e}")
        result["error"] = str(e)
    
    return result
 
 
def test_token_counting_comparison(file_path: str) -> Dict[str, Any]:
    """测试不同token计数方法的对比"""
    print(f"\n{'='*60}")
    print(f"Token计数方法对比: {file_path}")
    print(f"{'='*60}")
    
    result = {
        "file_path": file_path,
        "token_methods": {}
    }
    
    try:
        # 获取文档内容
        splitter = ContractSplitter()
        sections = splitter.split(file_path)
        flattened = splitter.flatten(sections)
        full_text = " ".join(flattened)
        
        # 测试不同的token计数方法
        methods = ["character"]
        
        # 检查是否有tiktoken
        try:
            import tiktoken
            methods.append("tiktoken")
            print("✓ tiktoken可用")
        except ImportError:
            print("✗ tiktoken不可用，仅使用字符计数")
        
        for method in methods:
            print(f"\n--- {method} 计数方法 ---")
            
            token_count = count_tokens(full_text, method)
            print(f"总token数: {token_count}")
            
            # 测试不同chunk大小的效果
            chunk_sizes = [500, 1000, 1500]
            method_result = {
                "total_tokens": token_count,
                "chunk_tests": {}
            }
            
            for chunk_size in chunk_sizes:
                chunks = sliding_window_split(
                    text=full_text,
                    max_tokens=chunk_size,
                    overlap=50,
                    by_sentence=True,
                    token_counter=method
                )
                
                method_result["chunk_tests"][f"size_{chunk_size}"] = {
                    "max_tokens": chunk_size,
                    "num_chunks": len(chunks),
                    "avg_tokens_per_chunk": round(sum(count_tokens(chunk, method) for chunk in chunks) / len(chunks), 2) if chunks else 0
                }
                
                print(f"  Chunk大小 {chunk_size}: {len(chunks)} 个chunks")
            
            result["token_methods"][method] = method_result
        
    except Exception as e:
        print(f"✗ Token计数测试失败: {e}")
        result["error"] = str(e)
    
    return result


def test_chinese_text_processing(file_path: str) -> Dict[str, Any]:
    """测试中文文本处理能力"""
    print(f"\n{'='*60}")
    print(f"中文文本处理测试: {file_path}")
    print(f"{'='*60}")

    result = {
        "file_path": file_path,
        "chinese_processing": {}
    }

    try:
        # 获取文档内容
        splitter = ContractSplitter()
        sections = splitter.split(file_path)
        flattened = splitter.flatten(sections)

        # 选择一个包含中文的chunk进行测试
        chinese_chunk = None
        for chunk in flattened:
            if any('\u4e00' <= char <= '\u9fff' for char in chunk):
                chinese_chunk = chunk
                break

        if chinese_chunk:
            print(f"✓ 找到中文内容，长度: {len(chinese_chunk)} 字符")

            # 测试中文句子分割
            sentences = split_chinese_sentences(chinese_chunk[:500])  # 取前500字符测试
            print(f"✓ 中文句子分割: {len(sentences)} 个句子")

            # 测试文本清理
            cleaned_text = clean_text(chinese_chunk[:200])
            print(f"✓ 文本清理完成")

            result["chinese_processing"] = {
                "has_chinese": True,
                "sample_length": len(chinese_chunk),
                "sentences_count": len(sentences),
                "sample_sentences": sentences[:3],  # 前3个句子
                "cleaned_sample": cleaned_text[:100] + "..." if len(cleaned_text) > 100 else cleaned_text
            }
        else:
            print("✗ 未找到中文内容")
            result["chinese_processing"] = {
                "has_chinese": False,
                "message": "文档中未检测到中文内容"
            }

    except Exception as e:
        print(f"✗ 中文处理测试失败: {e}")
        result["error"] = str(e)

    return result


def save_individual_chunks(file_path: str, test_results: Dict[str, Any], output_dir: str = "output"):
    """为单个文件保存chunks到独立文件，方便人工核对"""
    file_name = Path(file_path).stem
    safe_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_')).rstrip()

    # 创建文件专用目录
    file_output_dir = Path(output_dir) / "individual_chunks" / safe_name
    file_output_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []

    for strategy_name, strategy_result in test_results.items():
        if "error" in strategy_result:
            continue

        flattened_chunks = strategy_result.get("flattened_chunks", {})
        if not flattened_chunks or "chunks_preview" not in flattened_chunks:
            continue

        # 重新获取完整的chunks（preview只有前3个）
        try:
            # 根据文档类型选择处理方法
            if is_legal_document(file_path):
                # 使用法律文档专用切分器
                full_chunks = split_legal_document(
                    file_path,
                    max_tokens=strategy_result["max_tokens"]
                )
            else:
                # 重新处理以获取完整chunks
                splitter = ContractSplitter(
                    max_tokens=strategy_result["max_tokens"],
                    overlap=strategy_result["overlap"],
                    split_by_sentence=True,
                    token_counter="character"
                )
                sections = splitter.split(file_path)
                full_chunks = splitter.flatten(sections)

            # 保存chunks到文本文件（方便阅读）
            chunks_txt_file = file_output_dir / f"{strategy_name}_chunks.txt"
            with open(chunks_txt_file, 'w', encoding='utf-8') as f:
                f.write(f"文件: {file_path}\n")
                f.write(f"策略: {strategy_name}\n")
                f.write(f"参数: max_tokens={strategy_result['max_tokens']}, overlap={strategy_result['overlap']}\n")
                f.write(f"总chunks数: {len(full_chunks)}\n")
                f.write("=" * 80 + "\n\n")

                for i, chunk in enumerate(full_chunks):
                    f.write(f"【Chunk {i+1:03d}】 (长度: {len(chunk)} 字符)\n")
                    f.write("-" * 40 + "\n")
                    f.write(chunk)
                    f.write("\n" + "=" * 80 + "\n\n")

            # 保存chunks到JSON文件（方便程序处理）
            chunks_json_file = file_output_dir / f"{strategy_name}_chunks.json"
            chunks_data = {
                "file_path": file_path,
                "strategy": strategy_name,
                "parameters": {
                    "max_tokens": strategy_result["max_tokens"],
                    "overlap": strategy_result["overlap"]
                },
                "statistics": {
                    "total_chunks": len(full_chunks),
                    "avg_length": round(sum(len(chunk) for chunk in full_chunks) / len(full_chunks), 2) if full_chunks else 0,
                    "max_length": max(len(chunk) for chunk in full_chunks) if full_chunks else 0,
                    "min_length": min(len(chunk) for chunk in full_chunks) if full_chunks else 0
                },
                "chunks": [
                    {
                        "id": i + 1,
                        "content": chunk,
                        "length": len(chunk)
                    }
                    for i, chunk in enumerate(full_chunks)
                ]
            }

            with open(chunks_json_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, ensure_ascii=False, indent=2)

            saved_files.extend([str(chunks_txt_file), str(chunks_json_file)])

        except Exception as e:
            print(f"  ⚠️ 无法重新处理 {strategy_name}: {e}")

    return saved_files


def save_test_results(all_results: List[Dict[str, Any]], output_dir: str = "output"):
    """保存测试结果到文件"""
    print(f"\n{'='*60}")
    print("保存测试结果")
    print(f"{'='*60}")

    # 创建输出目录
    Path(output_dir).mkdir(exist_ok=True)

    # 生成时间戳
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # 保存详细结果
    detailed_file = f"{output_dir}/chunking_test_detailed_{timestamp}.json"
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"✓ 详细结果已保存: {detailed_file}")

    # 生成汇总报告
    summary_file = f"{output_dir}/chunking_test_summary_{timestamp}.md"
    generate_summary_report(all_results, summary_file)
    print(f"✓ 汇总报告已保存: {summary_file}")

    # 为每个文件单独保存chunks
    print(f"\n保存单独的chunks文件...")
    all_saved_files = []

    for result in all_results:
        if "error" in result:
            continue

        file_path = result["file_path"]
        test_results = result.get("test_results", {})

        if test_results:
            print(f"  📁 保存 {Path(file_path).name} 的chunks...")
            saved_files = save_individual_chunks(file_path, test_results, output_dir)
            all_saved_files.extend(saved_files)
            print(f"    ✓ 保存了 {len(saved_files)} 个文件")

    print(f"✓ 总共保存了 {len(all_saved_files)} 个单独的chunks文件")

    return detailed_file, summary_file


def generate_summary_report(all_results: List[Dict[str, Any]], output_file: str):
    """生成汇总报告"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Chunking测试汇总报告\n\n")
        f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # 总体统计
        f.write("## 总体统计\n\n")
        total_files = len(all_results)
        successful_files = sum(1 for r in all_results if "error" not in r)
        f.write(f"- 测试文件总数: {total_files}\n")
        f.write(f"- 成功处理文件: {successful_files}\n")
        f.write(f"- 失败文件: {total_files - successful_files}\n\n")

        # 按文件类型统计
        f.write("## 按文件类型统计\n\n")
        file_types = {}
        for result in all_results:
            ext = result.get("file_extension", "unknown")
            if ext not in file_types:
                file_types[ext] = {"total": 0, "success": 0}
            file_types[ext]["total"] += 1
            if "error" not in result:
                file_types[ext]["success"] += 1

        for ext, stats in file_types.items():
            f.write(f"- {ext}: {stats['success']}/{stats['total']} 成功\n")
        f.write("\n")

        # 详细结果
        f.write("## 详细结果\n\n")
        for i, result in enumerate(all_results):
            file_name = Path(result['file_path']).name
            safe_name = "".join(c for c in Path(result['file_path']).stem if c.isalnum() or c in (' ', '-', '_')).rstrip()

            f.write(f"### {i+1}. {file_name}\n\n")
            f.write(f"- 文件路径: `{result['file_path']}`\n")
            f.write(f"- 文件大小: {result.get('file_size', 0)} bytes\n")
            f.write(f"- 文件类型: {result.get('file_extension', 'unknown')}\n")

            if "error" in result:
                f.write(f"- ❌ 处理失败: {result['error']}\n\n")
                continue

            f.write("- ✅ 处理成功\n")
            f.write(f"- 📁 单独chunks文件: `output/individual_chunks/{safe_name}/`\n\n")

            # 测试策略结果
            if "test_results" in result:
                f.write("#### Chunking策略测试结果\n\n")
                for strategy_name, strategy_result in result["test_results"].items():
                    if "error" in strategy_result:
                        f.write(f"- **{strategy_name}**: ❌ {strategy_result['error']}\n")
                    else:
                        sections = strategy_result.get("hierarchical_sections", {}).get("num_sections", 0)
                        chunks = strategy_result.get("flattened_chunks", {}).get("num_chunks", 0)
                        time_taken = strategy_result.get("processing_time", 0)
                        f.write(f"- **{strategy_name}**: {sections} sections → {chunks} chunks ({time_taken}s)\n")
                        f.write(f"  - 📄 文本文件: `output/individual_chunks/{safe_name}/{strategy_name}_chunks.txt`\n")
                        f.write(f"  - 📊 JSON文件: `output/individual_chunks/{safe_name}/{strategy_name}_chunks.json`\n")
                f.write("\n")

            # Token计数结果
            if "token_methods" in result:
                f.write("#### Token计数方法对比\n\n")
                for method, method_result in result["token_methods"].items():
                    total_tokens = method_result.get("total_tokens", 0)
                    f.write(f"- **{method}**: {total_tokens} tokens\n")
                f.write("\n")

            # 中文处理结果
            if "chinese_processing" in result:
                chinese_result = result["chinese_processing"]
                if chinese_result.get("has_chinese", False):
                    sentences = chinese_result.get("sentences_count", 0)
                    f.write(f"#### 中文处理: ✅ 检测到中文，分割为 {sentences} 个句子\n\n")
                else:
                    f.write("#### 中文处理: ❌ 未检测到中文内容\n\n")

        # 添加人工核对指南
        f.write("## 📋 人工核对指南\n\n")
        f.write("每个成功处理的文件都有对应的chunks文件保存在 `output/individual_chunks/` 目录下：\n\n")
        f.write("### 文件结构\n")
        f.write("```\n")
        f.write("output/individual_chunks/\n")
        f.write("├── 文件名1/\n")
        f.write("│   ├── small_chunks_chunks.txt    # 小块策略的文本文件\n")
        f.write("│   ├── small_chunks_chunks.json   # 小块策略的JSON文件\n")
        f.write("│   ├── medium_chunks_chunks.txt   # 中块策略的文本文件\n")
        f.write("│   ├── medium_chunks_chunks.json  # 中块策略的JSON文件\n")
        f.write("│   ├── large_chunks_chunks.txt    # 大块策略的文本文件\n")
        f.write("│   └── large_chunks_chunks.json   # 大块策略的JSON文件\n")
        f.write("└── 文件名2/\n")
        f.write("    └── ...\n")
        f.write("```\n\n")
        f.write("### 核对要点\n\n")
        f.write("1. **内容完整性**: 检查是否有内容丢失或重复\n")
        f.write("2. **表格结构**: 验证表格内容是否正确提取和格式化\n")
        f.write("3. **中文处理**: 确认中文文本分割是否合理\n")
        f.write("4. **层次结构**: 检查章节标题和内容的对应关系\n")
        f.write("5. **chunk边界**: 验证chunk分割点是否合理（避免句子截断）\n\n")
        f.write("### 推荐核对流程\n\n")
        f.write("1. 先查看 `.txt` 文件进行快速浏览\n")
        f.write("2. 对比不同策略的分割效果\n")
        f.write("3. 重点检查表格密集的文档\n")
        f.write("4. 验证关键信息是否完整保留\n")


def run_comprehensive_tests():
    """运行综合测试"""
    print("🚀 开始综合Chunking测试")
    print("=" * 80)

    # 查找文档文件
    document_files = find_document_files()

    if not document_files:
        print("❌ 在output目录下未找到支持的文档文件 (.doc, .docx, .pdf)")
        print("请将测试文档放入output目录")
        return

    print(f"✅ 找到 {len(document_files)} 个文档文件:")
    for file in document_files:
        print(f"  - {file}")

    all_results = []

    # 对每个文件进行测试
    for i, file_path in enumerate(document_files):
        print(f"\n🔄 处理文件 {i+1}/{len(document_files)}: {Path(file_path).name}")

        # 基本chunking测试
        chunking_result = test_file_chunking(file_path)

        # Token计数对比测试
        token_result = test_token_counting_comparison(file_path)

        # 中文处理测试
        chinese_result = test_chinese_text_processing(file_path)

        # 合并结果
        combined_result = {
            **chunking_result,
            **token_result,
            **chinese_result
        }

        all_results.append(combined_result)

    # 保存结果
    detailed_file, summary_file = save_test_results(all_results)

    # 打印总结
    print(f"\n{'='*80}")
    print("🎉 测试完成!")
    print(f"{'='*80}")
    print(f"📊 详细结果: {detailed_file}")
    print(f"📋 汇总报告: {summary_file}")
    print(f"📁 总共测试了 {len(document_files)} 个文件")

    successful_count = sum(1 for r in all_results if "error" not in r)
    print(f"✅ 成功: {successful_count} 个文件")
    print(f"❌ 失败: {len(document_files) - successful_count} 个文件")

    return all_results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="综合Chunking测试工具")
    parser.add_argument("--file", "-f", help="测试单个文件")
    parser.add_argument("--output-dir", "-o", default="output", help="输出目录")

    args = parser.parse_args()

    if args.file:
        # 测试单个文件
        if not os.path.exists(args.file):
            print(f"❌ 文件不存在: {args.file}")
            return 1

        print(f"🔄 测试单个文件: {args.file}")
        result = test_file_chunking(args.file)

        # 保存单个文件结果
        output_file = f"{args.output_dir}/single_file_test_{Path(args.file).stem}.json"
        Path(args.output_dir).mkdir(exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"✅ 结果已保存: {output_file}")

        # 保存单独的chunks文件
        if "error" not in result and "test_results" in result:
            print(f"📁 保存单独的chunks文件...")
            saved_files = save_individual_chunks(args.file, result["test_results"], args.output_dir)
            print(f"✅ 保存了 {len(saved_files)} 个chunks文件:")
            for file_path in saved_files:
                print(f"  📄 {file_path}")
        else:
            print(f"⚠️ 文件处理失败，无法保存chunks")
    else:
        # 运行综合测试
        run_comprehensive_tests()

    return 0


if __name__ == "__main__":
    import datetime
    exit(main())


