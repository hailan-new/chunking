#!/usr/bin/env python3
"""
法律文档专业处理示例
演示如何使用Contract Splitter处理各种法律文档
"""

import sys
from pathlib import Path
import os

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def demo_legal_document_chunking():
    """演示法律文档专业分块"""
    print("⚖️ 法律文档专业分块")
    print("=" * 60)
    
    from contract_splitter.domain_helpers import split_legal_document
    
    # 测试不同类型的法律文档
    legal_docs = [
        ("output/law/中华人民共和国主席令第三十七号——中华人民共和国证券法（2019年修订）.pdf", "证券法"),
        ("output/law/附件1.关于修改《证券公司分类监管规定》的决定.pdf", "监管规定"),
        ("output/law/附件1.期货公司互联网营销管理暂行规定.pdf", "暂行规定"),
    ]
    
    for doc_path, doc_type in legal_docs:
        if not os.path.exists(doc_path):
            print(f"⚠️ {doc_type}文档不存在: {doc_path}")
            continue
        
        try:
            print(f"\n📄 处理{doc_type}: {Path(doc_path).name}")
            
            # 法律文档专业分块
            chunks = split_legal_document(
                doc_path,
                max_tokens=1200,           # 适合法律条文的分块大小
                strict_max_tokens=False,   # 允许超出以保持条文完整性
                legal_structure_detection=True  # 启用法律结构识别
            )
            
            print(f"   ✅ 分块完成: {len(chunks)} 个法律条文块")
            
            # 分析分块质量
            chunk_sizes = [len(chunk) for chunk in chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            max_size = max(chunk_sizes)
            min_size = min(chunk_sizes)
            
            print(f"   📊 分块统计:")
            print(f"      - 平均长度: {avg_size:.0f} 字符")
            print(f"      - 最大长度: {max_size} 字符")
            print(f"      - 最小长度: {min_size} 字符")
            
            # 检查法律条文识别
            article_chunks = 0
            chapter_chunks = 0
            
            for chunk in chunks:
                if "第" in chunk and "条" in chunk:
                    article_chunks += 1
                if "第" in chunk and "章" in chunk:
                    chapter_chunks += 1
            
            print(f"   🔍 法律结构识别:")
            print(f"      - 包含条文的块: {article_chunks}")
            print(f"      - 包含章节的块: {chapter_chunks}")
            
            # 显示前3个条文块示例
            print(f"   📝 条文块示例:")
            for i, chunk in enumerate(chunks[:3], 1):
                preview = chunk[:120] + "..." if len(chunk) > 120 else chunk
                print(f"      {i}. {preview}")
            
            if len(chunks) > 3:
                print(f"      ... 还有 {len(chunks) - 3} 个条文块")
                
        except Exception as e:
            print(f"   ❌ 处理失败: {str(e)}")


def demo_contract_analysis():
    """演示合同文档分析"""
    print("\n\n📋 合同文档分析")
    print("=" * 60)
    
    from contract_splitter import simple_chunk_file
    
    # 模拟合同文档内容（实际使用时替换为真实合同文档）
    contract_content = """
    甲方：某某公司
    乙方：某某个人
    
    第一条 合同目的
    为了明确双方的权利和义务，根据《中华人民共和国合同法》等相关法律法规，甲乙双方在平等、自愿的基础上，就相关事宜达成如下协议。
    
    第二条 合同标的
    甲方同意向乙方提供相关服务，乙方同意按照本合同约定支付相应费用。
    
    第三条 权利义务
    甲方权利：1. 按时收取费用；2. 监督服务质量。
    甲方义务：1. 提供优质服务；2. 保护客户信息。
    乙方权利：1. 享受约定服务；2. 监督服务质量。
    乙方义务：1. 按时支付费用；2. 配合服务提供。
    
    第四条 违约责任
    任何一方违反本合同约定，应承担相应的违约责任，并赔偿对方因此遭受的损失。
    """
    
    # 创建临时合同文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(contract_content)
        temp_contract = f.name
    
    try:
        print(f"📄 分析合同文档")
        
        # 使用句子完整性分块处理合同
        chunks = simple_chunk_file(
            temp_contract,
            max_chunk_size=300,
            overlap_ratio=0.1
        )
        
        print(f"   ✅ 合同分块: {len(chunks)} 个条款块")
        
        # 分析合同要素
        contract_elements = {
            "当事人": [],
            "合同条款": [],
            "权利义务": [],
            "违约责任": []
        }
        
        for chunk in chunks:
            content = chunk['content']
            
            # 识别当事人
            if "甲方" in content or "乙方" in content:
                contract_elements["当事人"].append(content[:100] + "...")
            
            # 识别合同条款
            if "第" in content and "条" in content:
                contract_elements["合同条款"].append(content[:100] + "...")
            
            # 识别权利义务
            if "权利" in content or "义务" in content:
                contract_elements["权利义务"].append(content[:100] + "...")
            
            # 识别违约责任
            if "违约" in content or "责任" in content:
                contract_elements["违约责任"].append(content[:100] + "...")
        
        # 显示分析结果
        print(f"   📊 合同要素分析:")
        for element_type, elements in contract_elements.items():
            print(f"      {element_type}: {len(elements)} 个相关块")
            for i, element in enumerate(elements[:2], 1):  # 只显示前2个
                print(f"         {i}. {element}")
            if len(elements) > 2:
                print(f"         ... 还有 {len(elements) - 2} 个")
    
    finally:
        # 清理临时文件
        os.unlink(temp_contract)


def demo_legal_excel_processing():
    """演示法律Excel表格处理"""
    print("\n\n📊 法律Excel表格处理")
    print("=" * 60)
    
    from contract_splitter import ExcelSplitter
    
    # 创建示例法律Excel文件
    import pandas as pd
    import tempfile
    
    # 模拟法律条文Excel数据
    legal_data = {
        '条文编号': ['第一条', '第二条', '第三条', '第四条'],
        '条文内容': [
            '为了规范证券公司分类监管，合理配置监管资源，提高监管效率，促进证券业健康发展，制定本规定。',
            '本规定适用于在中华人民共和国境内依法设立的证券公司。',
            '中国证监会及其派出机构依照本规定对证券公司进行分类监管。',
            '证券公司分类监管是指中国证监会根据证券公司风险管理能力、持续合规状况等因素进行的分类管理。'
        ],
        '适用范围': ['全部证券公司', '境内证券公司', '全部证券公司', '全部证券公司'],
        '监管部门': ['中国证监会', '中国证监会', '中国证监会及派出机构', '中国证监会']
    }
    
    # 创建临时Excel文件
    temp_excel = tempfile.mktemp(suffix='.xlsx')
    df = pd.DataFrame(legal_data)
    df.to_excel(temp_excel, index=False, sheet_name='法律条文')
    
    try:
        print(f"📄 处理法律Excel表格")
        
        # 使用Excel专业分块器
        splitter = ExcelSplitter(
            max_tokens=500,
            extract_mode="legal_content"  # 法律内容模式
        )
        
        sections = splitter.split(temp_excel)
        
        print(f"   ✅ Excel处理完成: {len(sections)} 个sections")
        
        # 分析Excel内容
        for i, section in enumerate(sections, 1):
            print(f"   📋 Section {i}:")
            print(f"      类型: {section.metadata.get('type', 'unknown')}")
            print(f"      工作表: {section.metadata.get('sheet_name', 'unknown')}")
            print(f"      内容长度: {len(section.content)} 字符")
            
            # 显示内容预览
            content_preview = section.content[:150] + "..." if len(section.content) > 150 else section.content
            print(f"      内容预览: {content_preview}")
            
            # 检查是否包含法律条文
            if "第" in section.content and "条" in section.content:
                print(f"      ✅ 包含法律条文")
            
    finally:
        # 清理临时文件
        os.unlink(temp_excel)


def demo_legal_structure_detection():
    """演示法律结构识别"""
    print("\n\n🔍 法律结构识别")
    print("=" * 60)
    
    from contract_splitter.utils import sliding_window_split
    
    # 测试法律文本
    legal_text = """
    第一章 总则
    
    第一条 为了规范证券公司分类监管，合理配置监管资源，提高监管效率，促进证券业健康发展，根据《证券法》、《证券公司监督管理条例》等法律法规，制定本规定。
    
    第二条 本规定适用于在中华人民共和国境内依法设立的证券公司。
    
    第二章 分类评价
    
    第三条 中国证监会及其派出机构依照本规定对证券公司进行分类监管。
    
    第四条 证券公司分类监管是指中国证监会根据证券公司风险管理能力、持续合规状况等因素，将证券公司分为不同类别，并据此对证券公司实施差别化监管的制度。
    
    第五条 证券公司分类评价每年进行一次，评价基准日为每年的12月31日。评价结果有效期为一年。
    """
    
    print(f"📄 法律文本结构识别")
    print(f"   文本长度: {len(legal_text)} 字符")
    
    # 使用句子优先分块，保持法律结构完整性
    chunks = sliding_window_split(
        legal_text,
        max_tokens=300,
        overlap=50,
        by_sentence=True,
        token_counter="character"
    )
    
    print(f"   ✅ 分块完成: {len(chunks)} 个chunks")
    
    # 分析法律结构
    structure_analysis = {
        "章节": 0,
        "条文": 0,
        "款项": 0,
        "完整句子": 0
    }
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n   📋 Chunk {i} ({len(chunk)}字符):")
        
        # 检查章节
        if "第" in chunk and "章" in chunk:
            structure_analysis["章节"] += 1
            print(f"      ✅ 包含章节标题")
        
        # 检查条文
        if "第" in chunk and "条" in chunk:
            structure_analysis["条文"] += 1
            print(f"      ✅ 包含法律条文")
        
        # 检查款项
        if "第" in chunk and ("款" in chunk or "项" in chunk):
            structure_analysis["款项"] += 1
            print(f"      ✅ 包含款项")
        
        # 检查句子完整性
        if chunk.strip().endswith(('。', '！', '？', '；')):
            structure_analysis["完整句子"] += 1
            print(f"      ✅ 句子完整结尾")
        
        # 显示内容预览
        content_preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
        print(f"      内容: {content_preview}")
    
    # 显示结构分析总结
    print(f"\n   📊 法律结构分析总结:")
    for structure_type, count in structure_analysis.items():
        print(f"      {structure_type}: {count}")
    
    sentence_completion_rate = structure_analysis["完整句子"] / len(chunks) * 100
    print(f"      句子完整率: {sentence_completion_rate:.1f}%")


def main():
    """主函数"""
    print("⚖️ 法律文档专业处理示例")
    print("=" * 80)
    print("本示例演示如何使用Contract Splitter处理各种法律文档")
    
    # 演示各种法律文档处理功能
    demo_legal_document_chunking()
    demo_contract_analysis()
    demo_legal_excel_processing()
    demo_legal_structure_detection()
    
    print(f"\n🎉 法律文档处理示例完成")
    print("=" * 80)
    print("💡 法律文档处理最佳实践:")
    print("1. 使用专业的法律文档分块接口保持条文完整性")
    print("2. 启用法律结构识别以获得更好的分块效果")
    print("3. 适当调整max_tokens参数以适应不同类型的法律文档")
    print("4. 对于Excel格式的法规表格，使用legal_content模式")
    print("5. 句子完整性优先，避免在条文中间截断")


if __name__ == "__main__":
    main()
