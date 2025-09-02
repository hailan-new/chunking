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
    
    doc_file = "output/TH-B-32天弘基金.信息系统运维管理制度（修订）V0.1_20170613.doc"
    
    if not os.path.exists(doc_file):
        print(f"✗ File not found: {doc_file}")
        return
    
    print(f"Testing MarkItDown conversion of: {doc_file}")
    print("=" * 60)
    
    # Step 1: Test MarkItDown conversion
    try:
        import markitdown
        from markitdown import MarkItDown
        from contract_splitter.converter import DocumentConverter

        
        # Convert using our current method
        converter = DocumentConverter()
        docx_path = converter.convert_to_docx(doc_file)
        print("Step 1: Converting with MarkItDown...")
        md = MarkItDown()
        result = md.convert(docx_path)
        
        print(f"✓ MarkItDown conversion successful")
        print(f"✓ Content length: {len(result.text_content)} characters")
        
        # Save the markdown result
        markdown_file = "output/test.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(result.text_content)
        print(f"✓ Markdown saved to: {markdown_file}")
        

        print(f"\nStep 2: Comparing with current method...")
        
        from contract_splitter.converter import DocumentConverter

        
        # Convert using our current method
        converter = DocumentConverter()
        docx_path = converter.convert_to_docx(doc_file)
        
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

