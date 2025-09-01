#!/usr/bin/env python3
"""
Demo script for contract_splitter package.

This script demonstrates how to use the contract splitter to process
various document types including Chinese contracts.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for importing contract_splitter
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract_splitter import ContractSplitter, split_document, flatten_sections


def create_sample_documents():
    """Create sample documents for testing."""
    
    # Create output directory
    output_dir = Path("sample_documents")
    output_dir.mkdir(exist_ok=True)
    
    # Sample Chinese contract content
    chinese_content = """
第一章 总则

第一条 合同目的
本合同是甲方与乙方就项目合作事宜达成的协议，旨在明确双方的权利和义务。

第二条 合同原则
双方应本着平等、自愿、公平、诚实信用的原则履行本合同。

第二章 合作内容

第三条 项目范围
甲方委托乙方完成以下工作：
1. 技术开发服务
2. 系统集成服务
3. 维护支持服务

第四条 技术要求
乙方应按照甲方提供的技术规范和要求完成项目开发。

第三章 权利义务

第五条 甲方权利义务
甲方有权监督项目进度，有义务按时支付费用。

第六条 乙方权利义务
乙方有权获得合理报酬，有义务按时完成项目交付。

第四章 费用支付

第七条 费用标准
项目总费用为人民币100万元。

第八条 支付方式
费用分三期支付：
（一）合同签订后支付30%
（二）项目中期验收后支付40%
（三）项目最终验收后支付30%

第五章 违约责任

第九条 违约情形
任何一方违反本合同约定，应承担违约责任。

第十条 违约后果
违约方应赔偿守约方因此遭受的损失。

第六章 争议解决

第十一条 争议处理
因本合同发生的争议，双方应友好协商解决。

第十二条 法律适用
本合同适用中华人民共和国法律。

第七章 附则

第十三条 合同生效
本合同自双方签字盖章之日起生效。

第十四条 合同变更
本合同的变更应经双方书面同意。
"""
    
    # Save sample content to a text file (simulating extracted content)
    with open(output_dir / "sample_chinese_contract.txt", "w", encoding="utf-8") as f:
        f.write(chinese_content)
    
    print(f"Sample documents created in {output_dir}")
    return output_dir


def demo_basic_usage():
    """Demonstrate basic usage of the contract splitter."""
    
    print("\n" + "="*60)
    print("DEMO: Basic Usage")
    print("="*60)
    
    # Create a simple splitter
    splitter = ContractSplitter(max_tokens=500, overlap=50)
    
    # Create sample text content
    sample_text = """
第一章 总则

第一条 合同目的
本合同是甲方与乙方就项目合作事宜达成的协议，旨在明确双方的权利和义务。双方应严格按照本合同条款执行，确保合作顺利进行。

第二条 合同原则
双方应本着平等、自愿、公平、诚实信用的原则履行本合同。任何一方不得利用优势地位损害对方利益。

第二章 合作内容

第三条 项目范围
甲方委托乙方完成技术开发、系统集成和维护支持等服务。项目应按照既定时间表和质量标准完成。
"""
    
    # Save to temporary file for demonstration
    temp_file = "temp_contract.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(sample_text)
    
    try:
        # This would work with actual DOCX/PDF files
        print("Note: This demo uses text content. For real usage, provide .docx or .pdf files.")
        print(f"Sample content length: {len(sample_text)} characters")
        
        # Demonstrate the splitting logic manually
        from contract_splitter.utils import split_by_natural_breakpoints
        chunks = split_by_natural_breakpoints(sample_text, 500, "character")
        
        print(f"Split into {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i+1} ({len(chunk)} chars):")
            print("-" * 40)
            print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
            
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)


def demo_advanced_features():
    """Demonstrate advanced features like different token counters."""
    
    print("\n" + "="*60)
    print("DEMO: Advanced Features")
    print("="*60)
    
    # Test different token counting methods
    sample_text = "这是一个中文合同示例。This is an English contract example."
    
    from contract_splitter.utils import count_tokens
    
    char_count = count_tokens(sample_text, "character")
    print(f"Character count: {char_count}")
    
    try:
        token_count = count_tokens(sample_text, "tiktoken")
        print(f"Token count (tiktoken): {token_count}")
    except:
        print("tiktoken not available, using character count")
    
    # Test Chinese sentence splitting
    from contract_splitter.utils import split_chinese_sentences
    
    chinese_text = "第一条规定了基本原则。第二条明确了双方责任。第三条约定了违约后果。"
    sentences = split_chinese_sentences(chinese_text)
    
    print(f"\nChinese sentence splitting:")
    print(f"Original: {chinese_text}")
    print(f"Split into {len(sentences)} sentences:")
    for i, sentence in enumerate(sentences):
        print(f"  {i+1}. {sentence}")


def demo_hierarchical_structure():
    """Demonstrate hierarchical section structure."""
    
    print("\n" + "="*60)
    print("DEMO: Hierarchical Structure")
    print("="*60)
    
    # Create a sample hierarchical structure
    sample_sections = [
        {
            "heading": "第一章 总则",
            "content": "本章规定了合同的基本原则和适用范围。",
            "level": 1,
            "subsections": [
                {
                    "heading": "第一条 合同目的",
                    "content": "本合同是甲方与乙方就项目合作事宜达成的协议。",
                    "level": 2,
                    "subsections": []
                },
                {
                    "heading": "第二条 合同原则", 
                    "content": "双方应本着平等、自愿、公平、诚实信用的原则履行本合同。",
                    "level": 2,
                    "subsections": []
                }
            ]
        },
        {
            "heading": "第二章 合作内容",
            "content": "本章详细说明了合作的具体内容和要求。",
            "level": 1,
            "subsections": [
                {
                    "heading": "第三条 项目范围",
                    "content": "甲方委托乙方完成技术开发、系统集成和维护支持等服务。",
                    "level": 2,
                    "subsections": []
                }
            ]
        }
    ]
    
    # Demonstrate flattening
    splitter = ContractSplitter()
    flattened = splitter.flatten(sample_sections)
    
    print("Hierarchical structure:")
    print(json.dumps(sample_sections, ensure_ascii=False, indent=2))
    
    print(f"\nFlattened into {len(flattened)} chunks:")
    for i, chunk in enumerate(flattened):
        print(f"\nChunk {i+1}:")
        print("-" * 40)
        print(chunk)


def demo_file_processing():
    """Demonstrate processing of actual files (if available)."""
    
    print("\n" + "="*60)
    print("DEMO: File Processing")
    print("="*60)
    
    # Look for sample files in current directory
    current_dir = Path(".")
    sample_files = []
    
    for ext in [".pdf", ".docx", ".doc"]:
        sample_files.extend(current_dir.glob(f"*{ext}"))
    
    if sample_files:
        print(f"Found {len(sample_files)} sample files:")
        for file in sample_files:
            print(f"  - {file}")
        
        # Try to process the first file
        sample_file = sample_files[0]
        print(f"\nTrying to process: {sample_file}")
        
        try:
            splitter = ContractSplitter(max_tokens=1000, overlap=100)
            sections = splitter.split(str(sample_file))
            
            print(f"Successfully split into {len(sections)} sections:")
            for i, section in enumerate(sections[:3]):  # Show first 3 sections
                print(f"\nSection {i+1}: {section.get('heading', 'No heading')}")
                content = section.get('content', '')
                print(f"Content preview: {content[:100]}...")
                
        except Exception as e:
            print(f"Error processing file: {e}")
            print("This is expected if required dependencies are not installed.")
    else:
        print("No sample files found in current directory.")
        print("To test file processing, place .pdf, .docx, or .doc files in this directory.")


def demo_error_handling():
    """Demonstrate error handling and edge cases."""
    
    print("\n" + "="*60)
    print("DEMO: Error Handling")
    print("="*60)
    
    splitter = ContractSplitter()
    
    # Test with non-existent file
    try:
        sections = splitter.split("non_existent_file.pdf")
    except FileNotFoundError as e:
        print(f"✓ Correctly handled missing file: {e}")
    
    # Test with unsupported file type
    try:
        sections = splitter.split("test.txt")
    except ValueError as e:
        print(f"✓ Correctly handled unsupported file type: {e}")
    
    # Test with empty content
    empty_sections = []
    flattened = splitter.flatten(empty_sections)
    print(f"✓ Handled empty sections: {len(flattened)} chunks")
    
    print("Error handling tests completed successfully!")


def main():
    """Run all demo functions."""
    
    print("Contract Splitter Package Demo")
    print("=" * 60)
    
    # Check dependencies
    from contract_splitter import check_dependencies
    deps = check_dependencies()
    
    print("Dependency Status:")
    for dep, available in deps.items():
        status = "✓" if available else "✗"
        print(f"  {status} {dep}")
    
    # Run demos
    demo_basic_usage()
    demo_advanced_features()
    demo_hierarchical_structure()
    demo_file_processing()
    demo_error_handling()
    
    print("\n" + "="*60)
    print("Demo completed! Check the output above for results.")
    print("="*60)


if __name__ == "__main__":
    main()
