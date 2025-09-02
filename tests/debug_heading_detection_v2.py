#!/usr/bin/env python3
"""
调试标题检测问题
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.docx_splitter import DocxSplitter


def test_heading_detection():
    """测试标题检测"""
    print("🔍 调试标题检测问题")
    print("=" * 80)
    
    splitter = DocxSplitter()
    
    # 测试一些具体的文本
    test_texts = [
        "（一）公司治理结构完善，内部控制有效 ;",
        "（二） 满足监管要求，未见监管部门（证监会、国家金融监督管理总局）针对该机构基金销售业务的停业整改处罚，确保该业务在监管允许范围内正常展业 ；",
        "（三）组织架构完整，设有专门的产品销售业务团队和分管销售业务的高管，销售业务团队的设置能保证业务运营的完整与独立，销售业务团队有满足营业需要的固定场所和安全防范措施 ;",
        "1、代销机构依法注册，并且持续经营；",
        "2、代销机构股权结构清晰，实际控制人信用情况良好；",
        "一、项目名称： 首创证券新增代销机构 - 广州农商行",
        "四、代销机构介绍—— 广州农村商业银行股份有限公司"
    ]
    
    for i, text in enumerate(test_texts):
        result = splitter._detect_heading_level_simple(text)
        print(f"测试 {i+1}:")
        print(f"  文本: {text[:50]}...")
        print(f"  长度: {len(text)}")
        print(f"  结果: is_heading={result['is_heading']}, level={result['level']}")
        print()


def test_actual_file():
    """测试实际文件的处理"""
    print("🔍 测试实际文件处理")
    print("=" * 80)
    
    test_file = "output/【立项申请】首创证券新增代销机构广州农商行的立项申请.doc"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    splitter = DocxSplitter()
    
    try:
        sections = splitter.split(test_file)
        print(f"✅ 分割成功: {len(sections)} 个sections")
        
        # 检查第一个section的结构
        if sections:
            section = sections[0]
            print(f"\n📋 第一个section:")
            print(f"  标题: {section.get('heading', 'N/A')}")
            print(f"  内容长度: {len(section.get('content', ''))}")
            print(f"  子sections数量: {len(section.get('subsections', []))}")
            
            # 检查子sections
            subsections = section.get('subsections', [])
            if subsections:
                print(f"\n📋 子sections:")
                for i, sub in enumerate(subsections[:5]):  # 只显示前5个
                    print(f"  {i+1}. 标题: {sub.get('heading', 'N/A')[:50]}...")
                    print(f"     内容长度: {len(sub.get('content', ''))}")
                    print(f"     子sections数量: {len(sub.get('subsections', []))}")
        
        # 检查包含问题的section
        for i, section in enumerate(sections):
            if "代销机构介绍" in section.get('heading', ''):
                print(f"\n🔍 检查section {i}: {section.get('heading', '')}")
                print(f"  内容长度: {len(section.get('content', ''))}")
                print(f"  子sections数量: {len(section.get('subsections', []))}")
                
                subsections = section.get('subsections', [])
                if subsections:
                    print(f"  子sections:")
                    for j, sub in enumerate(subsections):
                        heading = sub.get('heading', '')
                        content = sub.get('content', '')
                        print(f"    {j+1}. {heading[:30]}... (内容长度: {len(content)})")
                        
                        # 检查是否有重复
                        if heading in content:
                            print(f"       ⚠️  标题在内容中重复!")
                
                break
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    test_heading_detection()
    test_actual_file()


if __name__ == "__main__":
    main()
