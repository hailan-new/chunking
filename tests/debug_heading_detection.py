#!/usr/bin/env python3
"""
调试标题检测逻辑
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.docx_splitter import DocxSplitter


def debug_heading_detection():
    """调试标题检测逻辑"""
    print("🔍 调试标题检测逻辑")
    print("=" * 80)
    
    # 创建DocxSplitter
    splitter = DocxSplitter(max_tokens=2000, overlap=200)
    
    # 测试一些示例文本
    test_texts = [
        "一、项目名称： 首创证券新增代销机构 - 广州农商行",  # 26字符
        "（一）公司治理结构完善，内部控制有效",  # 短文本
        "（二）满足监管要求，未见监管部门（证监会、国家金融监督管理总局）针对该机构基金销售业务的停业整改处罚，确保该业务在监管允许范围内正常展业",  # 长文本
        "（三）组织架构完整，设有专门的产品销售业务团队和分管销售业务的高管，销售业务团队的设置能保证业务运营的完整与独立，销售业务团队有满足营业需要的固定场所和安全防范措施",  # 很长文本
        "五、风险管理措施",  # 短标题
        "（一）操作风险 : 标准流程手册化运营的操作风险管理体系\n资产管理是一个长链条的业务，涉及到众多环节..."  # 长内容
    ]
    
    print("🔧 测试_detect_heading_level_simple方法:")
    for i, text in enumerate(test_texts):
        print(f"\n测试文本 {i+1}:")
        print(f"  长度: {len(text)} 字符")
        print(f"  前50字符: {text[:50]}...")
        
        result = splitter._detect_heading_level_simple(text)
        print(f"  结果: is_heading={result['is_heading']}, level={result['level']}")
        
        # 检查是否以标题标记开头
        starts_with_marker = False
        if text.startswith(('一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、', '九、', '十、')):
            starts_with_marker = True
            print(f"  ✅ 以一级标记开头")
        elif text.startswith(('（一）', '（二）', '（三）', '（四）', '（五）', '（六）', '（七）', '（八）', '（九）', '（十）')):
            starts_with_marker = True
            print(f"  ✅ 以二级标记开头")
        else:
            print(f"  ❌ 不以标题标记开头")
        
        # 分析为什么会有这个结果
        if len(text) > 50 and result['is_heading']:
            print(f"  ⚠️  警告: 文本超过50字符但仍被标记为标题!")
        elif len(text) <= 50 and starts_with_marker and not result['is_heading']:
            print(f"  ⚠️  警告: 短文本有标题标记但未被标记为标题!")


def main():
    """主函数"""
    print("🚀 标题检测调试")
    print("=" * 80)
    
    debug_heading_detection()
    
    print("\n" + "=" * 80)
    print("🎯 调试完成")


if __name__ == "__main__":
    main()
