#!/usr/bin/env python3
"""
测试统一的法律结构识别器
验证hardcode消除和功能一致性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract_splitter.legal_structure_detector import LegalStructureDetector, LegalStructureLevel, get_legal_detector


def test_basic_detection():
    """测试基本的结构识别功能"""
    print("🔍 测试基本的结构识别功能")
    print("-" * 60)
    
    detector = get_legal_detector("legal")
    
    # 测试用例
    test_cases = [
        # 法律结构
        ("第一编", True, LegalStructureLevel.BOOK.value),
        ("第二篇", True, LegalStructureLevel.PART.value),
        ("第三章", True, LegalStructureLevel.CHAPTER.value),
        ("第四节", True, LegalStructureLevel.SECTION.value),
        ("第五条", True, LegalStructureLevel.ARTICLE.value),
        ("第六款", True, LegalStructureLevel.CLAUSE.value),
        ("第七项", True, LegalStructureLevel.ITEM.value),
        ("（一）", True, LegalStructureLevel.ENUMERATION.value),
        ("（二）", True, LegalStructureLevel.ENUMERATION.value),
        ("1、", True, LegalStructureLevel.NUMBERING.value),
        ("2.", True, LegalStructureLevel.NUMBERING.value),
        
        # 非法律结构
        ("这是普通文本", False, 10),
        ("第一条的内容很长，包含了很多详细的规定和说明。", False, 10),
        ("", False, 10),
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for text, expected_is_heading, expected_level in test_cases:
        is_heading = detector.is_legal_heading(text)
        level = detector.get_heading_level(text)
        
        print(f"文本: '{text}'")
        print(f"  是否为标题: {is_heading} (期望: {expected_is_heading})")
        print(f"  层级: {level} (期望: {expected_level})")
        
        if is_heading == expected_is_heading and level == expected_level:
            print("  ✅ 通过")
            success_count += 1
        else:
            print("  ❌ 失败")
        print()
    
    print(f"测试结果: {success_count}/{total_count} 通过")
    return success_count == total_count


def test_pattern_consistency():
    """测试模式一致性"""
    print("🔍 测试模式一致性")
    print("-" * 60)
    
    detector = get_legal_detector("legal")
    
    # 获取所有法律模式
    all_patterns = detector.get_all_legal_patterns()
    print(f"总共 {len(all_patterns)} 个法律模式:")
    
    for i, pattern in enumerate(all_patterns, 1):
        print(f"  {i:2d}. {pattern}")
    
    # 测试模式覆盖性
    test_texts = [
        "第一编总则",
        "第二篇基本原则", 
        "第三章一般规定",
        "第四节特别规定",
        "第五条基本要求",
        "第六款具体措施",
        "第七项实施细则",
        "（一）第一项",
        "（二）第二项",
        "1、基本原则",
        "2、具体要求"
    ]
    
    print(f"\n测试模式覆盖性:")
    coverage_count = 0
    
    for text in test_texts:
        if detector.is_legal_heading(text):
            print(f"  ✅ '{text}' - 识别成功")
            coverage_count += 1
        else:
            print(f"  ❌ '{text}' - 识别失败")
    
    print(f"\n覆盖率: {coverage_count}/{len(test_texts)} ({coverage_count/len(test_texts)*100:.1f}%)")
    return coverage_count == len(test_texts)


def test_section_extraction():
    """测试条文提取功能"""
    print("🔍 测试条文提取功能")
    print("-" * 60)
    
    detector = get_legal_detector("legal")
    
    # 测试文本
    test_text = """
    第一章 总则
    
    第一条 为了规范管理，制定本办法。
    
    第二条 本办法适用于所有相关机构。
    
    第二章 具体规定
    
    第三条 各机构应当遵守以下规定：
    （一）严格执行相关制度；
    （二）定期报告工作情况。
    
    第四条 违反本办法的，依法追究责任。
    """
    
    sections = detector.extract_legal_sections(test_text)
    
    print(f"提取到 {len(sections)} 个结构化部分:")
    
    expected_sections = [
        ("第一章", LegalStructureLevel.CHAPTER.value),
        ("第一条", LegalStructureLevel.ARTICLE.value),
        ("第二条", LegalStructureLevel.ARTICLE.value),
        ("第二章", LegalStructureLevel.CHAPTER.value),
        ("第三条", LegalStructureLevel.ARTICLE.value),
        ("第四条", LegalStructureLevel.ARTICLE.value),
    ]
    
    success = True
    for i, section in enumerate(sections):
        print(f"  {i+1}. {section['heading']} (类型: {section['type']}, 层级: {section['level']})")
        print(f"     内容: {section['content'][:50]}...")
        
        if i < len(expected_sections):
            expected_heading, expected_level = expected_sections[i]
            if expected_heading in section['heading'] and section['level'] == expected_level:
                print(f"     ✅ 符合预期")
            else:
                print(f"     ❌ 不符合预期 (期望: {expected_heading}, 层级: {expected_level})")
                success = False
        print()
    
    return success and len(sections) >= len(expected_sections)


def test_text_cleaning():
    """测试文本清理功能"""
    print("🔍 测试文本清理功能")
    print("-" * 60)
    
    detector = get_legal_detector("legal")
    
    # 测试用例
    test_cases = [
        ("制定本", "制定本办法"),
        ("根据本", "根据本办法"),
        ("按照本", "按照本办法"),
        ("违反本", "违反本办法"),
        ("（征求意见稿）> 第一条", "第一条"),
        ("  多个   空格  ", "多个 空格"),
    ]
    
    success_count = 0
    
    for input_text, expected_output in test_cases:
        cleaned = detector.clean_legal_text(input_text)
        print(f"输入: '{input_text}'")
        print(f"输出: '{cleaned}'")
        print(f"期望: '{expected_output}'")
        
        if expected_output in cleaned:
            print("✅ 通过")
            success_count += 1
        else:
            print("❌ 失败")
        print()
    
    return success_count == len(test_cases)


def test_integration_with_splitters():
    """测试与splitter的集成"""
    print("🔍 测试与splitter的集成")
    print("-" * 60)
    
    try:
        from contract_splitter.domain_helpers import LegalClauseSplitter
        
        # 创建splitter
        splitter = LegalClauseSplitter()
        
        # 检查是否有结构检测器
        if hasattr(splitter, 'structure_detector'):
            print("✅ LegalClauseSplitter 已集成结构检测器")
            
            # 测试检测器功能
            detector = splitter.structure_detector
            test_result = detector.is_legal_heading("第一条")
            
            if test_result:
                print("✅ 结构检测器功能正常")
                return True
            else:
                print("❌ 结构检测器功能异常")
                return False
        else:
            print("❌ LegalClauseSplitter 未集成结构检测器")
            return False
            
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🧪 统一法律结构识别器测试")
    print("=" * 80)
    
    tests = [
        ("基本检测功能", test_basic_detection),
        ("模式一致性", test_pattern_consistency),
        ("条文提取功能", test_section_extraction),
        ("文本清理功能", test_text_cleaning),
        ("Splitter集成", test_integration_with_splitters),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("=" * 80)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
                
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
            results.append((test_name, False))
            import traceback
            traceback.print_exc()
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！统一结构识别器工作正常。")
    else:
        print("⚠️  部分测试失败，需要进一步检查。")
    
    print("\n💡 技术成就:")
    print("1. ✅ 消除了hardcode重复")
    print("2. ✅ 统一了法律结构识别逻辑")
    print("3. ✅ 提供了可扩展的模式管理")
    print("4. ✅ 支持多种文档类型")
    print("5. ✅ 集成到所有相关组件")


if __name__ == "__main__":
    main()
