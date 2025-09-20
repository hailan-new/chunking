#!/usr/bin/env python3
"""
测试修复后的split_legal_document函数对Excel文件的处理
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from contract_splitter import split_legal_document

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_split_legal_document_excel():
    """测试split_legal_document函数处理Excel文件"""
    # 用户文件路径
    user_file = os.path.expanduser("~/Downloads/0-358831BWGZJWJ.xlsx")
    
    if not os.path.exists(user_file):
        logger.error(f"文件不存在: {user_file}")
        return False
    
    logger.info(f"测试split_legal_document函数处理: {user_file}")
    
    try:
        # 使用split_legal_document函数
        chunks = split_legal_document(user_file)
        
        logger.info(f"生成的块数量: {len(chunks)}")
        
        # 分析块的内容
        import re

        # 检测第一个块是否是法规名称（通常较短且不包含"第X条"）
        first_chunk = chunks[0] if chunks else ""
        is_law_name = (
            len(first_chunk) < 100 and
            "条例" in first_chunk and
            not re.search(r'第[一二三四五六七八九十百千万\d]+条', first_chunk)
        )

        # 检测条文块（包含"第X条"）
        article_chunks = []
        for chunk in chunks:
            if re.search(r'^第[一二三四五六七八九十百千万\d]+条', chunk):
                article_chunks.append(chunk)

        for i, chunk in enumerate(chunks[:10]):  # 只显示前10个块
            logger.info(f"\n--- 块 {i+1} ---")
            logger.info(f"长度: {len(chunk)} 字符")

            # 检查块类型
            if i == 0 and is_law_name:
                logger.info("✅ 检测到法规名称块")
                logger.info(f"内容: {chunk}")
            elif re.search(r'^第[一二三四五六七八九十百千万\d]+条', chunk):
                logger.info("✅ 检测到条文块")
                # 提取条文号
                article_match = re.search(r'^(第[一二三四五六七八九十百千万\d]+条)', chunk)
                if article_match:
                    article_num = article_match.group(1)
                    logger.info(f"条文号: {article_num}")
                logger.info(f"内容预览: {chunk[:100]}...")
            else:
                logger.info("ℹ️  其他格式块")
                logger.info(f"内容预览: {chunk[:100]}...")

        # 检查是否成功应用了law_articles模式
        law_name_chunks = [first_chunk] if is_law_name else []
        
        logger.info(f"\n📊 统计结果:")
        logger.info(f"法规名称块: {len(law_name_chunks)}")
        logger.info(f"条文块: {len(article_chunks)}")
        logger.info(f"总块数: {len(chunks)}")
        
        if len(law_name_chunks) > 0 and len(article_chunks) > 0:
            logger.info("✅ 成功应用了law_articles模式！")
            
            # 显示法规名称
            if law_name_chunks:
                law_name_content = law_name_chunks[0].replace("【LAW_NAME】", "").strip()
                logger.info(f"法规名称: {law_name_content}")
            
            return True
        else:
            logger.error("❌ 未能正确应用law_articles模式")
            return False
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    logger.info("🧪 测试修复后的split_legal_document函数")
    success = test_split_legal_document_excel()
    
    if success:
        logger.info("\n🎉 测试成功！split_legal_document现在可以正确处理Excel法律文档了。")
    else:
        logger.error("\n❌ 测试失败！")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
