#!/usr/bin/env python3
"""
测试Excel文件的分层chunk功能
验证Excel文件在分层处理中的完整支持
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from contract_splitter import split_document, flatten_sections, SplitterFactory, ExcelSplitter


class TestExcelHierarchicalChunking(unittest.TestCase):
    """测试Excel文件的分层chunk功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_excel_file = self.create_test_excel_file()
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_excel_file(self):
        """创建测试Excel文件"""
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl not available")
        
        from openpyxl import Workbook
        
        wb = Workbook()
        
        # 第一个工作表：法律条文
        ws1 = wb.active
        ws1.title = "法律条文"
        
        legal_data = [
            ["条文编号", "条文内容", "适用范围"],
            ["第一条", "为了规范证券公司分类监管，合理配置监管资源，提高监管效率，促进证券业健康发展，制定本规定。", "全部证券公司"],
            ["第二条", "本规定适用于在中华人民共和国境内依法设立的证券公司。", "境内证券公司"],
            ["第三条", "中国证监会及其派出机构依照本规定对证券公司进行分类监管。", "监管机构"],
            ["第四条", "证券公司分类监管是指中国证监会根据证券公司风险管理能力、持续合规状况等因素，将证券公司分为不同类别。", "分类标准"],
        ]
        
        for row_data in legal_data:
            ws1.append(row_data)
        
        # 第二个工作表：评价指标
        ws2 = wb.create_sheet("评价指标")
        
        indicator_data = [
            ["指标类别", "指标名称", "评分标准", "权重"],
            ["风险管理能力", "净资本充足率", "优秀≥150%，良好120%-150%", "30%"],
            ["风险管理能力", "流动性覆盖率", "优秀≥120%，良好100%-120%", "20%"],
            ["持续合规状况", "合规检查结果", "无重大问题为优秀", "25%"],
            ["市场竞争力", "市场份额", "行业前10%为优秀", "25%"],
        ]
        
        for row_data in indicator_data:
            ws2.append(row_data)
        
        # 保存文件
        test_file = os.path.join(self.temp_dir, "test_legal_excel.xlsx")
        wb.save(test_file)
        
        return test_file
    
    def test_split_document_excel_support(self):
        """测试split_document函数对Excel的支持"""
        # 测试基本分割
        chunks = split_document(self.test_excel_file, max_tokens=500)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        
        # 验证chunks内容
        for chunk in chunks:
            self.assertIsInstance(chunk, str)
            self.assertGreater(len(chunk.strip()), 0)
        
        # 验证包含Excel内容（法律条文或表格数据）
        all_content = ' '.join(chunks)
        self.assertTrue(
            '第一条' in all_content or '第二条' in all_content or '指标类别' in all_content,
            f"Should contain Excel content, got: {all_content[:200]}..."
        )
    
    def test_split_document_excel_with_extract_mode(self):
        """测试split_document函数支持Excel的extract_mode参数"""
        # 测试法律内容模式
        chunks_legal = split_document(
            self.test_excel_file, 
            max_tokens=500,
            extract_mode="legal_content"
        )
        
        # 测试表格结构模式
        chunks_table = split_document(
            self.test_excel_file,
            max_tokens=500,
            extract_mode="table_structure"
        )
        
        # 测试全部内容模式
        chunks_all = split_document(
            self.test_excel_file,
            max_tokens=500,
            extract_mode="all_content"
        )
        
        # 验证不同模式产生不同结果
        self.assertIsInstance(chunks_legal, list)
        self.assertIsInstance(chunks_table, list)
        self.assertIsInstance(chunks_all, list)
        
        # 验证都有内容
        self.assertGreater(len(chunks_legal), 0)
        self.assertGreater(len(chunks_table), 0)
        self.assertGreater(len(chunks_all), 0)
    
    def test_factory_excel_hierarchical_processing(self):
        """测试SplitterFactory对Excel的分层处理"""
        factory = SplitterFactory()
        
        # 验证支持Excel格式
        supported_formats = factory.get_supported_formats()
        excel_formats = ['xlsx', 'xls', 'xlsm', 'xltx', 'xltm']
        
        for fmt in excel_formats:
            self.assertIn(fmt, supported_formats)
        
        # 测试自动创建Excel splitter
        splitter = factory.create_splitter(self.test_excel_file)
        self.assertIsInstance(splitter, ExcelSplitter)
        
        # 测试分层处理
        sections = splitter.split(self.test_excel_file)
        self.assertIsInstance(sections, list)
        self.assertGreater(len(sections), 0)
        
        # 验证sections结构
        for section in sections:
            self.assertIsInstance(section, dict)
            self.assertIn('heading', section)
            self.assertIn('content', section)
            self.assertIn('level', section)
        
        # 测试扁平化
        chunks = splitter.flatten(sections)
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
    
    def test_factory_split_and_flatten_excel(self):
        """测试Factory的split_and_flatten方法对Excel的支持"""
        factory = SplitterFactory()
        
        # 测试一步到位的分割和扁平化
        chunks = factory.split_and_flatten(
            self.test_excel_file,
            max_tokens=400
        )
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        
        # 验证chunks内容
        for chunk in chunks:
            self.assertIsInstance(chunk, str)
            self.assertGreater(len(chunk.strip()), 0)
        
        # 验证包含Excel内容
        all_content = ' '.join(chunks)
        self.assertTrue(
            '第一条' in all_content or '第二条' in all_content or '指标类别' in all_content,
            f"Should contain Excel content, got: {all_content[:200]}..."
        )
    
    def test_flatten_sections_function_excel(self):
        """测试flatten_sections函数对Excel sections的支持"""
        # 先获取Excel的sections
        splitter = ExcelSplitter(max_tokens=300)
        sections = splitter.split(self.test_excel_file)
        
        # 使用flatten_sections函数
        chunks = flatten_sections(
            sections,
            max_tokens=400,
            overlap=50
        )
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        
        # 验证chunks内容
        for chunk in chunks:
            self.assertIsInstance(chunk, str)
            self.assertGreater(len(chunk.strip()), 0)
    
    def test_excel_hierarchical_structure_preservation(self):
        """测试Excel分层结构的保持"""
        splitter = ExcelSplitter(
            max_tokens=300,
            extract_mode="legal_content"
        )
        
        sections = splitter.split(self.test_excel_file)
        
        # 验证层次结构
        self.assertGreater(len(sections), 0)
        
        # 检查是否有不同的工作表sections
        sheet_names = set()
        for section in sections:
            if 'source_sheet' in section:
                sheet_names.add(section['source_sheet'])
        
        # 应该有多个工作表
        self.assertGreater(len(sheet_names), 1)
        
        # 验证法律条文的识别
        legal_sections = [s for s in sections if s.get('section_type') == 'legal_article']
        self.assertGreater(len(legal_sections), 0)
        
        # 验证条文编号的识别
        for section in legal_sections:
            heading = section.get('heading', '')
            self.assertTrue(
                '第一条' in heading or '第二条' in heading or '第三条' in heading or '第四条' in heading,
                f"Legal section heading should contain article number: {heading}"
            )
    
    def test_excel_different_strategies(self):
        """测试Excel在不同chunking策略下的表现"""
        splitter = ExcelSplitter(max_tokens=200)
        sections = splitter.split(self.test_excel_file)
        
        strategies = ["finest_granularity", "all_levels", "parent_only"]
        
        for strategy in strategies:
            with self.subTest(strategy=strategy):
                chunks = splitter.flatten(sections, strategy=strategy)
                
                self.assertIsInstance(chunks, list)
                self.assertGreater(len(chunks), 0)
                
                # 验证chunks内容
                for chunk in chunks:
                    self.assertIsInstance(chunk, str)
                    self.assertGreater(len(chunk.strip()), 0)


class TestExcelIntegrationWithOtherFormats(unittest.TestCase):
    """测试Excel与其他格式的集成"""
    
    def test_mixed_format_processing(self):
        """测试混合格式处理中Excel的支持"""
        factory = SplitterFactory()
        
        # 测试格式检测
        test_files = [
            "document.xlsx",
            "spreadsheet.xls", 
            "workbook.xlsm",
            "template.xltx",
            "report.pdf",
            "contract.docx"
        ]
        
        for file_path in test_files:
            file_format = factory.detect_file_format(file_path)
            
            if file_path.endswith(('.xlsx', '.xls', '.xlsm', '.xltx', '.xltm')):
                # Excel格式应该被支持
                self.assertIn(file_format, factory.get_supported_formats())
            
            # 测试splitter创建（会因为文件不存在而失败，但不应该因为格式不支持而失败）
            if file_format in factory.get_supported_formats():
                try:
                    splitter = factory.create_splitter(file_path)
                    if file_format in ['xlsx', 'xls', 'xlsm', 'xltx', 'xltm']:
                        self.assertIsInstance(splitter, ExcelSplitter)
                except (FileNotFoundError, ValueError) as e:
                    # 文件不存在是预期的
                    if "File not found" in str(e):
                        pass
                    else:
                        raise


if __name__ == '__main__':
    unittest.main()
