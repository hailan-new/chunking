#!/usr/bin/env python3
"""
测试用户提供的Excel文件：0-358831BWGZJWJ.xlsx
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from contract_splitter.excel_processor import ExcelProcessor
from contract_splitter.excel_splitter import ExcelSplitter

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_user_excel_file():
    """测试用户的Excel文件"""
    # 用户文件路径
    user_file = os.path.expanduser("~/Downloads/0-358831BWGZJWJ.xlsx")
    
    if not os.path.exists(user_file):
        logger.error(f"文件不存在: {user_file}")
        return False
    
    logger.info(f"开始测试文件: {user_file}")
    
    try:
        # 1. 首先用ExcelProcessor测试不同的提取模式
        processor = ExcelProcessor()
        
        logger.info("\n" + "="*80)
        logger.info("📊 测试不同的提取模式")
        logger.info("="*80)
        
        # 测试普通法律内容模式
        logger.info("\n--- 1. legal_content 模式 ---")
        legal_content = processor.extract_text(user_file, extract_mode="legal_content")
        if legal_content:
            logger.info(f"提取长度: {len(legal_content)} 字符")
            logger.info("内容预览:")
            print(legal_content[:500] + "..." if len(legal_content) > 500 else legal_content)
        
        # 测试新的法律条文模式
        logger.info("\n--- 2. law_articles 模式 ---")
        law_articles_content = processor.extract_text(user_file, extract_mode="law_articles")
        if law_articles_content:
            logger.info(f"提取长度: {len(law_articles_content)} 字符")
            logger.info("内容预览:")
            print(law_articles_content[:800] + "..." if len(law_articles_content) > 800 else law_articles_content)
        
        # 2. 使用ExcelSplitter测试分块效果
        logger.info("\n" + "="*80)
        logger.info("🔪 测试分块效果")
        logger.info("="*80)
        
        # 测试普通法律内容分块
        logger.info("\n--- legal_content 分块 ---")
        legal_splitter = ExcelSplitter(extract_mode="legal_content", max_tokens=1000)
        legal_chunks = legal_splitter.split(user_file)
        
        logger.info(f"生成块数: {len(legal_chunks)}")
        for i, chunk in enumerate(legal_chunks[:3]):  # 只显示前3个块
            logger.info(f"\n块 {i+1}:")
            logger.info(f"  标题: {chunk.get('heading', 'N/A')}")
            logger.info(f"  类型: {chunk.get('section_type', 'N/A')}")
            logger.info(f"  内容长度: {len(chunk.get('content', ''))}")
            logger.info(f"  内容预览: {chunk.get('content', '')[:100]}...")
        
        # 测试新的法律条文分块
        logger.info("\n--- law_articles 分块 ---")
        articles_splitter = ExcelSplitter(extract_mode="law_articles", max_tokens=1000)
        articles_chunks = articles_splitter.split(user_file)
        
        logger.info(f"生成块数: {len(articles_chunks)}")
        
        # 分析块类型
        law_name_chunks = [c for c in articles_chunks if c.get('section_type') == 'law_name']
        law_article_chunks = [c for c in articles_chunks if c.get('section_type') == 'law_article']
        other_chunks = [c for c in articles_chunks if c.get('section_type') not in ['law_name', 'law_article']]
        
        logger.info(f"法规名称块: {len(law_name_chunks)}")
        logger.info(f"法律条文块: {len(law_article_chunks)}")
        logger.info(f"其他类型块: {len(other_chunks)}")
        
        # 显示所有块的详细信息
        for i, chunk in enumerate(articles_chunks):
            logger.info(f"\n块 {i+1}:")
            logger.info(f"  标题: {chunk.get('heading', 'N/A')}")
            logger.info(f"  类型: {chunk.get('section_type', 'N/A')}")
            logger.info(f"  内容长度: {len(chunk.get('content', ''))}")
            logger.info(f"  工作表: {chunk.get('source_sheet', 'N/A')}")
            content = chunk.get('content', '')
            if len(content) > 150:
                logger.info(f"  内容预览: {content[:150]}...")
            else:
                logger.info(f"  内容: {content}")
        
        # 3. 判断是否检测到特殊格式
        logger.info("\n" + "="*80)
        logger.info("🔍 格式检测结果")
        logger.info("="*80)
        
        if len(law_name_chunks) > 0:
            logger.info("✅ 检测到特殊法规-条文格式")
            logger.info(f"   - 法规名称: {law_name_chunks[0].get('content', 'N/A')}")
            logger.info(f"   - 条文数量: {len(law_article_chunks)}")
        else:
            logger.info("ℹ️  未检测到特殊法规-条文格式，使用普通处理")
        
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    logger.info("🧪 开始测试用户Excel文件")
    success = test_user_excel_file()
    
    if success:
        logger.info("\n🎉 测试完成！")
    else:
        logger.error("\n❌ 测试失败！")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
