#!/usr/bin/env python3

import sys
import os

# Test MarkItDown import and basic functionality
print("Testing MarkItDown...")

try:
    from markitdown import MarkItDown
    print("✓ MarkItDown imported successfully")
    
    # Test with the doc file
    doc_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if os.path.exists(doc_file):
        print(f"✓ Found file: {doc_file}")
        
        md = MarkItDown()
        print("✓ MarkItDown instance created")
        
        result = md.convert(doc_file)
        print(f"✓ Conversion successful, content length: {len(result.text_content)}")
        
        # Save result
        output_file = "output/markitdown_result.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.text_content)
        print(f"✓ Saved to: {output_file}")
        
        # Show preview
        print("\nPreview (first 500 chars):")
        print("-" * 40)
        print(result.text_content[:500])
        print("-" * 40)
        
    else:
        print(f"✗ File not found: {doc_file}")
        
except ImportError as e:
    print(f"✗ Import failed: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
