#!/usr/bin/env python3
"""
Test script to convert and process the .doc file with enhanced table extraction.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, '.')

from contract_splitter.converter import DocumentConverter
from contract_splitter.docx_splitter import DocxSplitter

def test_doc_conversion():
    """Test conversion and processing of the .doc file."""
    
    doc_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(doc_file):
        print(f"✗ File not found: {doc_file}")
        return
    
    print(f"Testing conversion and processing of: {doc_file}")
    print("=" * 60)
    
    # Step 1: Test conversion
    converter = DocumentConverter()
    
    try:
        print("Step 1: Converting .doc to .docx...")
        docx_path = converter.convert_to_docx(doc_file)
        print(f"✓ Conversion successful: {docx_path}")
        
        # Check file size
        if os.path.exists(docx_path):
            size = os.path.getsize(docx_path)
            print(f"✓ Output file size: {size} bytes")
        else:
            print("✗ Output file not found")
            return
            
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return
    
    # Step 2: Test processing with enhanced table extraction
    try:
        print("\nStep 2: Processing with enhanced table extraction...")
        splitter = DocxSplitter(max_tokens=1000, overlap=100)
        sections = splitter.split(docx_path)
        
        print(f"✓ Processing successful: {len(sections)} sections")
        
        # Show section details
        for i, section in enumerate(sections[:5]):  # Show first 5 sections
            print(f"\nSection {i+1}: {section.get('title', 'Untitled')}")
            content = section.get('content', '')
            if content:
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"  Content preview: {preview}")
            else:
                print("  Content: (empty)")
                
            # Check for subsections
            subsections = section.get('subsections', [])
            if subsections:
                print(f"  Subsections: {len(subsections)}")
                for j, subsection in enumerate(subsections[:3]):  # Show first 3 subsections
                    sub_content = subsection.get('content', '')
                    if sub_content:
                        sub_preview = sub_content[:100] + "..." if len(sub_content) > 100 else sub_content
                        print(f"    {j+1}. {subsection.get('title', 'Untitled')}: {sub_preview}")
        
        # Step 3: Flatten and save results
        print(f"\nStep 3: Flattening sections...")
        chunks = splitter.flatten(sections)
        print(f"✓ Flattened into {len(chunks)} chunks")
        
        # Save results
        import json
        output_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请_enhanced.json"

        # Prepare data for saving
        result_data = {
            'metadata': {
                'source_file': doc_file,
                'converted_file': docx_path,
                'total_sections': len(sections),
                'total_chunks': len(chunks),
                'processing_method': 'enhanced_table_extraction'
            },
            'sections': sections,
            'chunks': chunks
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"✓ Results saved to: {output_file}")
        
        # Show sample chunks with table content
        print(f"\nSample chunks (showing table content):")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i+1} (length: {len(chunk)} chars):")
            if "表格" in chunk or "项目" in chunk or "客户" in chunk:
                print(f"  {chunk}")
            else:
                preview = chunk[:150] + "..." if len(chunk) > 150 else chunk
                print(f"  {preview}")
                
    except Exception as e:
        print(f"✗ Processing failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        converter.cleanup()
        print(f"\n✓ Cleanup completed")

if __name__ == "__main__":
    test_doc_conversion()
