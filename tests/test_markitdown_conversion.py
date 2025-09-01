#!/usr/bin/env python3
"""
Test script to convert and process the .doc file using MarkItDown for better table structure preservation.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, '.')

def test_markitdown_conversion():
    """Test conversion using MarkItDown for better table structure."""
    
    doc_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(doc_file):
        print(f"✗ File not found: {doc_file}")
        return
    
    print(f"Testing MarkItDown conversion of: {doc_file}")
    print("=" * 60)
    
    # Step 1: Test MarkItDown conversion
    try:
        import markitdown
        from markitdown import MarkItDown
        
        print("Step 1: Converting with MarkItDown...")
        md = MarkItDown()
        result = md.convert(doc_file)
        
        print(f"✓ MarkItDown conversion successful")
        print(f"✓ Content length: {len(result.text_content)} characters")
        
        # Save the markdown result
        markdown_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请_markitdown.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(result.text_content)
        print(f"✓ Markdown saved to: {markdown_file}")
        
        # Show preview of the content
        print(f"\nContent preview (first 1000 chars):")
        print("-" * 40)
        print(result.text_content[:1000])
        print("-" * 40)
        
        # Look for table structures
        lines = result.text_content.split('\n')
        table_lines = [line for line in lines if '|' in line and line.strip()]
        
        if table_lines:
            print(f"\n✓ Found {len(table_lines)} table-like lines")
            print("Sample table lines:")
            for i, line in enumerate(table_lines[:10]):  # Show first 10 table lines
                print(f"  {i+1}. {line.strip()}")
        else:
            print("\n⚠ No clear table structures found in markdown")
            
        # Check for specific content we expect
        expected_content = [
            "项目名称",
            "首创证券新增代销机构",
            "广州农商行",
            "客户名称",
            "广州农村商业银行",
            "业务类型"
        ]
        
        found_content = []
        for content in expected_content:
            if content in result.text_content:
                found_content.append(content)
        
        print(f"\n✓ Found {len(found_content)}/{len(expected_content)} expected content items:")
        for content in found_content:
            print(f"  ✓ {content}")
        
        missing_content = [c for c in expected_content if c not in found_content]
        if missing_content:
            print(f"\n⚠ Missing content:")
            for content in missing_content:
                print(f"  ✗ {content}")
                
    except ImportError:
        print("✗ MarkItDown not available. Install with: pip install markitdown")
        return
    except Exception as e:
        print(f"✗ MarkItDown conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Compare with our current method
    try:
        print(f"\nStep 2: Comparing with current method...")
        
        from contract_splitter.converter import DocumentConverter
        from contract_splitter.docx_splitter import DocxSplitter
        
        # Convert using our current method
        converter = DocumentConverter()
        docx_path = converter.convert_to_docx(doc_file)
        
        splitter = DocxSplitter(max_tokens=1000, overlap=100)
        sections = splitter.split(docx_path)
        chunks = splitter.flatten(sections)
        
        # Get all content from current method
        current_content = " ".join(chunks)
        
        print(f"✓ Current method content length: {len(current_content)} characters")
        print(f"✓ MarkItDown content length: {len(result.text_content)} characters")
        
        # Compare content coverage
        markitdown_found = sum(1 for content in expected_content if content in result.text_content)
        current_found = sum(1 for content in expected_content if content in current_content)
        
        print(f"\nContent coverage comparison:")
        print(f"  MarkItDown: {markitdown_found}/{len(expected_content)} items")
        print(f"  Current method: {current_found}/{len(expected_content)} items")
        
        if markitdown_found > current_found:
            print("✓ MarkItDown found more content!")
        elif current_found > markitdown_found:
            print("✓ Current method found more content!")
        else:
            print("= Both methods found the same amount of content")
            
        # Cleanup
        converter.cleanup()
        
    except Exception as e:
        print(f"✗ Comparison failed: {e}")
        import traceback
        traceback.print_exc()

def test_markitdown_with_chunking():
    """Test MarkItDown with our chunking system."""
    
    markdown_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请_markitdown.md"
    
    if not os.path.exists(markdown_file):
        print(f"✗ Markdown file not found: {markdown_file}")
        print("Run test_markitdown_conversion() first")
        return
    
    print(f"\nStep 3: Processing MarkItDown output with chunking...")
    
    try:
        # Read the markdown content
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Simple chunking based on markdown structure
        chunks = []
        current_chunk = ""
        max_chunk_size = 1000
        
        lines = markdown_content.split('\n')
        
        for line in lines:
            # Check if adding this line would exceed chunk size
            if len(current_chunk) + len(line) > max_chunk_size and current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        print(f"✓ Created {len(chunks)} chunks from MarkItDown output")
        
        # Save the chunked results
        import json
        
        result_data = {
            'metadata': {
                'source_file': "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc",
                'processing_method': 'markitdown_conversion',
                'total_chunks': len(chunks),
                'original_length': len(markdown_content)
            },
            'chunks': chunks
        }
        
        output_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请_markitdown_chunks.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Chunked results saved to: {output_file}")
        
        # Show sample chunks
        print(f"\nSample chunks:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i+1} (length: {len(chunk)} chars):")
            preview = chunk[:200] + "..." if len(chunk) > 200 else chunk
            print(f"  {preview}")
            
    except Exception as e:
        print(f"✗ Chunking failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_markitdown_conversion()
    test_markitdown_with_chunking()
