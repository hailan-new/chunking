#!/usr/bin/env python3
"""
调试完整的处理流程
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.docx_splitter import DocxSplitter


def debug_processing_flow():
    """调试完整的处理流程"""
    print("🔍 调试完整的处理流程")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 创建DocxSplitter
    splitter = DocxSplitter(max_tokens=2000, overlap=200)
    
    print("📄 步骤1: 调用split方法")
    try:
        sections = splitter.split(test_file)
        print(f"✅ 得到 {len(sections)} 个sections")
        
        # 分析每个section
        for i, section in enumerate(sections):
            print(f"\n📋 Section {i+1}:")
            print(f"   标题: {section.get('heading', 'N/A')}")
            print(f"   内容长度: {len(section.get('content', ''))}")
            print(f"   子章节数: {len(section.get('subsections', []))}")
            
            content = section.get('content', '')
            if content:
                preview = content[:200].replace('\n', ' ')
                print(f"   内容预览: {preview}...")
                
                # 检查是否包含关键内容
                if "一、项目名称" in content:
                    print(f"   ✅ 包含项目名称")
                if "广州金融控股" in content:
                    print(f"   ✅ 包含股东信息")
        
        print(f"\n📄 步骤2: 调用flatten方法")
        chunks = splitter.flatten(sections)
        print(f"✅ 得到 {len(chunks)} 个chunks")
        
        # 分析每个chunk
        for i, chunk in enumerate(chunks):
            print(f"\n📋 Chunk {i+1}:")
            print(f"   长度: {len(chunk)} 字符")
            
            if "一、项目名称" in chunk:
                print(f"   ✅ 包含项目名称")
            if "广州金融控股" in chunk:
                print(f"   ✅ 包含股东信息")
            
            preview = chunk[:200].replace('\n', ' ')
            print(f"   预览: {preview}...")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🚀 处理流程调试")
    print("=" * 80)
    
    debug_processing_flow()
    
    print("\n" + "=" * 80)
    print("🎯 调试完成")


if __name__ == "__main__":
    main()
