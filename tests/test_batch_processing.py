#!/usr/bin/env python3
"""
批量处理output目录下的分类文件
根据不同子目录采用适当的helper函数进行拆分测试
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.splitter_factory import SplitterFactory, get_default_factory
from contract_splitter.domain_helpers import (
    split_legal_document,
    split_contract,
    split_regulation,
    LegalClauseSplitter,
    DomainContractSplitter,
    RegulationSplitter
)


# WPS和PDF处理现在集成到DocxSplitter中，不需要单独的转换函数


def get_directory_helper_config(directory_name: str) -> Dict[str, Any]:
    """
    根据目录名称获取相应的helper配置
    
    Args:
        directory_name: 目录名称
        
    Returns:
        配置字典
    """
    configs = {
        "contract": {
            "helper_type": "contract",
            "contract_type": "general",
            "description": "合同文件"
        },
        "law": {
            "helper_type": "legal",
            "description": "法律法规文件"
        },
        "rule": {
            "helper_type": "regulation",
            "regulation_type": "general",
            "description": "规章制度文件"
        },
        "others": {
            "helper_type": "general",
            "description": "其他文件"
        }
    }
    
    return configs.get(directory_name, configs["others"])


def save_chunks_to_file(file_path: str, chunks: List[str], output_dir: str = "output/chunks") -> str:
    """
    将chunks保存到单独的文件中

    Args:
        file_path: 原文件路径
        chunks: chunks列表
        output_dir: 输出目录

    Returns:
        输出文件路径
    """
    from datetime import datetime

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 生成输出文件名
    file_name = os.path.basename(file_path)
    base_name = os.path.splitext(file_name)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"{base_name}_chunks_{timestamp}.txt")

    # 写入chunks
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"文档: {file_name}\n")
        f.write(f"原文件路径: {file_path}\n")
        f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总chunks数: {len(chunks)}\n")
        f.write("=" * 80 + "\n\n")

        for i, chunk in enumerate(chunks, 1):
            f.write(f"Chunk {i}:\n")
            f.write("-" * 40 + "\n")
            f.write(chunk)
            f.write("\n\n" + "=" * 80 + "\n\n")

    return output_file


def process_single_file(file_path: str, config: Dict[str, Any], max_tokens: int = 3000, output_dir: str = "output/chunks") -> Dict[str, Any]:
    """
    处理单个文件
    
    Args:
        file_path: 文件路径
        config: 处理配置
        max_tokens: 最大token数
        
    Returns:
        处理结果
    """
    result = {
        "file_path": file_path,
        "success": False,
        "chunks_count": 0,
        "error": None,
        "output_files": []
    }
    
    try:
        # 使用工厂模式检查文件支持
        factory = get_default_factory()
        file_info = factory.get_file_info(file_path)

        if not file_info['supported']:
            result["error"] = f"不支持的文件格式: {file_info['format']}"
            return result

        print(f"🔄 处理{file_info['format'].upper()}文件: {file_path}")
        print(f"   使用处理器: {file_info['splitter_class']}")
        
        # 根据配置选择处理方法
        helper_type = config.get("helper_type", "general")
        
        if helper_type == "legal":
            print(f"⚖️ 使用法律条款切分器处理: {file_path}")
            chunks = split_legal_document(
                file_path,
                max_tokens=max_tokens,
                strict_max_tokens=True
            )

        elif helper_type == "contract":
            contract_type = config.get("contract_type", "general")
            print(f"📄 使用合同切分器处理 ({contract_type}): {file_path}")
            chunks = split_contract(
                file_path,
                contract_type=contract_type,
                max_tokens=max_tokens,
                strict_max_tokens=True
            )

        elif helper_type == "regulation":
            regulation_type = config.get("regulation_type", "general")
            print(f"📋 使用规章制度切分器处理 ({regulation_type}): {file_path}")
            chunks = split_regulation(
                file_path,
                regulation_type=regulation_type,
                max_tokens=max_tokens,
                strict_max_tokens=True
            )

        else:
            print(f"📄 使用工厂模式自动选择处理器: {file_path}")
            # 使用工厂模式自动选择合适的splitter
            chunks = factory.split_and_flatten(
                file_path,
                max_tokens=max_tokens,
                strict_max_tokens=True
            )
        
        # 保存所有chunks到单个文件
        if chunks:
            output_file = save_chunks_to_file(file_path, chunks, output_dir)
            result["output_files"].append(output_file)
        
        result["success"] = True
        result["chunks_count"] = len(chunks)
        
        print(f"✅ 处理成功: {len(chunks)} 个chunks")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ 处理失败: {e}")
    
    return result


def scan_and_process_directory(base_dir: str = "output", max_tokens: int = 3000, output_dir: str = "output/chunks") -> Dict[str, Any]:
    """
    扫描并处理目录下的所有文件
    
    Args:
        base_dir: 基础目录
        max_tokens: 最大token数
        
    Returns:
        处理结果汇总
    """
    results = {
        "total_files": 0,
        "successful_files": 0,
        "failed_files": 0,
        "total_chunks": 0,
        "directory_results": {},
        "errors": []
    }
    
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"❌ 目录不存在: {base_dir}")
        return results
    
    # 扫描所有子目录
    for subdir in base_path.iterdir():
        if not subdir.is_dir():
            continue
        
        subdir_name = subdir.name
        config = get_directory_helper_config(subdir_name)
        
        print(f"\n📁 处理目录: {subdir_name} ({config['description']})")
        print("=" * 80)
        
        dir_results = {
            "config": config,
            "files": [],
            "total_files": 0,
            "successful_files": 0,
            "total_chunks": 0
        }
        
        # 处理目录中的所有文件
        for file_path in subdir.iterdir():
            if file_path.is_file():
                file_ext = file_path.suffix.lower()
                
                # 支持的文件格式
                if file_ext in ['.docx', '.doc', '.wps', '.pdf']:
                    print(f"\n📄 处理文件: {file_path.name}")
                    
                    file_result = process_single_file(str(file_path), config, max_tokens, output_dir)
                    dir_results["files"].append(file_result)
                    dir_results["total_files"] += 1
                    results["total_files"] += 1
                    
                    if file_result["success"]:
                        dir_results["successful_files"] += 1
                        dir_results["total_chunks"] += file_result["chunks_count"]
                        results["successful_files"] += 1
                        results["total_chunks"] += file_result["chunks_count"]
                    else:
                        results["failed_files"] += 1
                        results["errors"].append({
                            "file": str(file_path),
                            "error": file_result["error"]
                        })
        
        results["directory_results"][subdir_name] = dir_results
        
        print(f"\n📊 {subdir_name} 目录处理完成:")
        print(f"  总文件数: {dir_results['total_files']}")
        print(f"  成功处理: {dir_results['successful_files']}")
        print(f"  生成chunks: {dir_results['total_chunks']}")
    
    return results


def main():
    """主函数"""
    print("🚀 批量文档处理测试")
    print("=" * 80)
    print("📋 配置:")
    print(f"  最大token数: 3000")
    print(f"  严格chunk控制: 启用")

    # 显示工厂模式支持的格式
    factory = get_default_factory()
    supported_formats = factory.get_supported_formats()
    print(f"  支持格式: {', '.join(supported_formats).upper()}")

    # 显示格式能力
    capabilities = factory.get_format_capabilities()
    print("  处理器映射:")
    for format_type, info in capabilities.items():
        print(f"    {format_type.upper()}: {info['splitter_class']}")
    
    # 开始处理
    output_chunks_dir = "output/chunks"
    print(f"  输出目录: {output_chunks_dir}")
    results = scan_and_process_directory("output", max_tokens=3000, output_dir=output_chunks_dir)
    
    # 输出汇总结果
    print("\n" + "=" * 80)
    print("📊 处理结果汇总")
    print("=" * 80)
    print(f"总文件数: {results['total_files']}")
    print(f"成功处理: {results['successful_files']}")
    print(f"处理失败: {results['failed_files']}")
    print(f"总chunks数: {results['total_chunks']}")
    
    # 按目录显示结果
    for dir_name, dir_result in results["directory_results"].items():
        print(f"\n📁 {dir_name} ({dir_result['config']['description']}):")
        print(f"  文件数: {dir_result['total_files']}")
        print(f"  成功: {dir_result['successful_files']}")
        print(f"  Chunks: {dir_result['total_chunks']}")
    
    # 显示错误
    if results["errors"]:
        print(f"\n❌ 处理失败的文件:")
        for error in results["errors"]:
            print(f"  {error['file']}: {error['error']}")
    
    # 保存详细结果到JSON文件
    output_file = "output/batch_processing_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细结果已保存到: {output_file}")


if __name__ == "__main__":
    main()
