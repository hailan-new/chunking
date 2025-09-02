#!/usr/bin/env python3
"""
测试嵌套表格提取功能
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter import ContractSplitter


def test_nested_table_extraction():
    """测试嵌套表格提取功能"""
    print("🔍 测试嵌套表格提取功能")
    print("=" * 60)
    
    # 测试文件
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    try:
        # 创建分割器
        splitter = ContractSplitter(
            max_tokens=1000,
            overlap=100,
            split_by_sentence=True,
            token_counter="character"
        )
        
        # 分割文档
        print(f"📄 处理文件: {test_file}")
        sections = splitter.split(test_file)
        flattened = splitter.flatten(sections)
        
        print(f"✅ 成功分割为 {len(flattened)} 个chunks")
        
        # 查找包含嵌套表格的chunks
        nested_table_chunks = []
        expected_shareholders = [
            "广州金融控股集团有限公司",
            "广州地铁集团有限公司", 
            "广州城市更新集团有限公司",
            "广州数字科技集团有限公司",
            "广州市建设投资发展有限公司",
            "广州工业投资控股集团有限公司",
            "广州万力集团有限公司",
            "广州开发区工业发展集团有限公司",
            "百年人寿保险股份有限公司",
            "美林投资有限公司"
        ]
        
        for i, chunk in enumerate(flattened):
            if "【嵌套表格" in chunk:
                nested_table_chunks.append((i, chunk))
        
        print(f"🔍 找到 {len(nested_table_chunks)} 个包含嵌套表格的chunks")
        
        # 验证股东信息是否完整提取
        all_shareholders_found = True
        missing_shareholders = []
        
        for shareholder in expected_shareholders:
            found = False
            for chunk_idx, chunk in nested_table_chunks:
                if shareholder in chunk:
                    found = True
                    break
            
            if not found:
                all_shareholders_found = False
                missing_shareholders.append(shareholder)
        
        # 输出测试结果
        print("\n📊 测试结果:")
        print("-" * 40)
        
        if all_shareholders_found:
            print("✅ 所有预期的股东信息都已成功提取")
            print(f"✅ 成功提取了 {len(expected_shareholders)} 个股东的信息")
        else:
            print(f"❌ 缺失 {len(missing_shareholders)} 个股东信息:")
            for shareholder in missing_shareholders:
                print(f"   - {shareholder}")
        
        # 显示嵌套表格内容示例
        if nested_table_chunks:
            print(f"\n📋 嵌套表格内容示例 (Chunk {nested_table_chunks[0][0] + 1}):")
            print("-" * 40)
            chunk_content = nested_table_chunks[0][1]
            
            # 提取嵌套表格部分
            start_marker = "【嵌套表格1】"
            end_marker = "【嵌套表格结束】"
            
            start_idx = chunk_content.find(start_marker)
            end_idx = chunk_content.find(end_marker)
            
            if start_idx != -1 and end_idx != -1:
                nested_content = chunk_content[start_idx:end_idx + len(end_marker)]
                print(nested_content)
            else:
                print("未找到完整的嵌套表格标记")
        
        return all_shareholders_found
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 嵌套表格提取功能测试")
    print("=" * 80)
    
    success = test_nested_table_extraction()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 测试通过！嵌套表格提取功能正常工作")
    else:
        print("❌ 测试失败！嵌套表格提取功能需要进一步优化")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
