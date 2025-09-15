#!/usr/bin/env python3
"""
Excel文档处理器
专门处理Excel文件(.xlsx, .xls, .xlsm)，提取结构化内容并针对法律文档进行优化
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import tempfile

logger = logging.getLogger(__name__)


class ExcelProcessor:
    """
    Excel文档处理器
    支持多种Excel格式，提供文本提取和结构化处理功能
    """
    
    def __init__(self):
        """初始化Excel处理器"""
        self.available_libraries = self._check_available_libraries()
        logger.info(f"Excel处理器初始化完成，可用库: {list(self.available_libraries.keys())}")
    
    def _check_available_libraries(self) -> Dict[str, bool]:
        """检查可用的Excel处理库"""
        libraries = {
            'openpyxl': False,
            'xlrd': False,
            'pandas': False,
            'xlwings': False
        }
        
        # 检查openpyxl (推荐用于.xlsx)
        try:
            import openpyxl
            libraries['openpyxl'] = True
            logger.info("✓ openpyxl可用 - 支持.xlsx/.xlsm文件")
        except ImportError:
            logger.warning("✗ openpyxl不可用")
        
        # 检查xlrd (用于.xls)
        try:
            import xlrd
            libraries['xlrd'] = True
            logger.info("✓ xlrd可用 - 支持.xls文件")
        except ImportError:
            logger.warning("✗ xlrd不可用")
        
        # 检查pandas (通用处理)
        try:
            import pandas as pd
            libraries['pandas'] = True
            logger.info("✓ pandas可用 - 通用Excel处理")
        except ImportError:
            logger.warning("✗ pandas不可用")
        
        # 检查xlwings (Windows Excel COM)
        try:
            import xlwings
            libraries['xlwings'] = True
            logger.info("✓ xlwings可用 - Windows Excel COM支持")
        except ImportError:
            pass  # xlwings是可选的
        
        return libraries
    
    def is_excel_file(self, file_path: str) -> bool:
        """
        检测文件是否为Excel格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            True表示是Excel文件
        """
        if not os.path.exists(file_path):
            return False
        
        # 检查文件扩展名
        ext = Path(file_path).suffix.lower()
        excel_extensions = ['.xlsx', '.xls', '.xlsm', '.xltx', '.xltm']
        
        if ext in excel_extensions:
            return True
        
        # 检查文件头（ZIP格式检测）
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                # Excel 2007+ 文件是ZIP格式
                if header == b'PK\x03\x04':
                    return True
                # Excel 97-2003 文件头
                elif header[:2] == b'\xd0\xcf':
                    return True
        except Exception:
            pass
        
        return False
    
    def extract_text(self, file_path: str, extract_mode: str = "legal_content") -> Optional[str]:
        """
        从Excel文件提取文本内容
        
        Args:
            file_path: Excel文件路径
            extract_mode: 提取模式 ("legal_content", "table_structure", "all_content")
            
        Returns:
            提取的文本内容，失败返回None
        """
        if not self.is_excel_file(file_path):
            logger.error(f"不是有效的Excel文件: {file_path}")
            return None
        
        file_ext = Path(file_path).suffix.lower()
        
        # 根据文件类型选择处理方法
        if file_ext in ['.xlsx', '.xlsm', '.xltx', '.xltm']:
            return self._extract_from_xlsx(file_path, extract_mode)
        elif file_ext == '.xls':
            return self._extract_from_xls(file_path, extract_mode)
        else:
            logger.warning(f"不支持的Excel格式: {file_ext}")
            return None
    
    def _extract_from_xlsx(self, file_path: str, extract_mode: str) -> Optional[str]:
        """从.xlsx/.xlsm文件提取文本"""
        # 优先使用openpyxl
        if self.available_libraries.get('openpyxl'):
            try:
                return self._extract_with_openpyxl(file_path, extract_mode)
            except Exception as e:
                logger.warning(f"openpyxl提取失败: {e}")
        
        # 备选：使用pandas
        if self.available_libraries.get('pandas'):
            try:
                return self._extract_with_pandas(file_path, extract_mode)
            except Exception as e:
                logger.warning(f"pandas提取失败: {e}")
        
        logger.error(f"无法处理Excel文件: {file_path}")
        return None
    
    def _extract_from_xls(self, file_path: str, extract_mode: str) -> Optional[str]:
        """从.xls文件提取文本"""
        # 优先使用xlrd
        if self.available_libraries.get('xlrd'):
            try:
                return self._extract_with_xlrd(file_path, extract_mode)
            except Exception as e:
                logger.warning(f"xlrd提取失败: {e}")
        
        # 备选：使用pandas
        if self.available_libraries.get('pandas'):
            try:
                return self._extract_with_pandas(file_path, extract_mode)
            except Exception as e:
                logger.warning(f"pandas提取失败: {e}")
        
        logger.error(f"无法处理Excel文件: {file_path}")
        return None
    
    def _extract_with_openpyxl(self, file_path: str, extract_mode: str) -> str:
        """使用openpyxl提取内容"""
        import openpyxl
        
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        text_parts = []
        
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            
            # 添加工作表标题
            text_parts.append(f"【工作表: {sheet_name}】")
            
            if extract_mode == "legal_content":
                sheet_text = self._extract_legal_content_openpyxl(sheet)
            elif extract_mode == "table_structure":
                sheet_text = self._extract_table_structure_openpyxl(sheet)
            else:  # all_content
                sheet_text = self._extract_all_content_openpyxl(sheet)
            
            if sheet_text:
                text_parts.append(sheet_text)
        
        workbook.close()
        return '\n\n'.join(text_parts)
    
    def _extract_legal_content_openpyxl(self, sheet) -> str:
        """提取法律相关内容（优化版）"""
        content_parts = []
        
        # 法律文档关键词
        legal_keywords = ['条', '款', '项', '章', '节', '编', '篇', '规定', '办法', '条例', '法律', '法规']
        
        for row in sheet.iter_rows(values_only=True):
            if not any(row):  # 跳过空行
                continue
            
            row_text = []
            for cell_value in row:
                if cell_value is not None:
                    cell_str = str(cell_value).strip()
                    if cell_str:
                        row_text.append(cell_str)
            
            if row_text:
                row_content = " | ".join(row_text)
                
                # 检查是否包含法律关键词
                if any(keyword in row_content for keyword in legal_keywords):
                    content_parts.append(f"★ {row_content}")  # 标记重要内容
                else:
                    content_parts.append(row_content)
        
        return '\n'.join(content_parts)
    
    def _extract_table_structure_openpyxl(self, sheet) -> str:
        """提取表格结构"""
        content_parts = []
        
        # 获取有数据的区域
        if sheet.max_row == 1 and sheet.max_column == 1:
            return ""
        
        # 处理表头
        header_row = []
        for cell in sheet[1]:
            if cell.value is not None:
                header_row.append(str(cell.value).strip())
            else:
                header_row.append("")
        
        if any(header_row):
            content_parts.append(f"表头: {' | '.join(header_row)}")
            content_parts.append("-" * 50)
        
        # 处理数据行
        for row_num in range(2, min(sheet.max_row + 1, 1000)):  # 限制行数避免过大
            row_data = []
            for cell in sheet[row_num]:
                if cell.value is not None:
                    row_data.append(str(cell.value).strip())
                else:
                    row_data.append("")
            
            if any(row_data):
                content_parts.append(" | ".join(row_data))
        
        return '\n'.join(content_parts)
    
    def _extract_all_content_openpyxl(self, sheet) -> str:
        """提取所有内容"""
        content_parts = []
        
        for row in sheet.iter_rows(values_only=True):
            if not any(row):
                continue
            
            row_text = []
            for cell_value in row:
                if cell_value is not None:
                    row_text.append(str(cell_value).strip())
            
            if row_text:
                content_parts.append(" | ".join(row_text))
        
        return '\n'.join(content_parts)
    
    def _extract_with_xlrd(self, file_path: str, extract_mode: str) -> str:
        """使用xlrd提取内容（用于.xls文件）"""
        import xlrd
        
        workbook = xlrd.open_workbook(file_path)
        text_parts = []
        
        for sheet_name in workbook.sheet_names():
            sheet = workbook.sheet_by_name(sheet_name)
            
            text_parts.append(f"【工作表: {sheet_name}】")
            
            content_parts = []
            for row_idx in range(sheet.nrows):
                row_data = []
                for col_idx in range(sheet.ncols):
                    cell_value = sheet.cell_value(row_idx, col_idx)
                    if cell_value:
                        row_data.append(str(cell_value).strip())
                
                if row_data:
                    content_parts.append(" | ".join(row_data))
            
            if content_parts:
                text_parts.append('\n'.join(content_parts))
        
        return '\n\n'.join(text_parts)
    
    def _extract_with_pandas(self, file_path: str, extract_mode: str) -> str:
        """使用pandas提取内容（通用方法）"""
        import pandas as pd
        
        try:
            # 读取所有工作表
            excel_file = pd.ExcelFile(file_path)
            text_parts = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                text_parts.append(f"【工作表: {sheet_name}】")
                
                # 转换为文本
                content_parts = []
                for _, row in df.iterrows():
                    row_data = []
                    for value in row:
                        if pd.notna(value):
                            row_data.append(str(value).strip())
                    
                    if row_data:
                        content_parts.append(" | ".join(row_data))
                
                if content_parts:
                    text_parts.append('\n'.join(content_parts))
            
            return '\n\n'.join(text_parts)
            
        except Exception as e:
            logger.error(f"pandas处理Excel失败: {e}")
            raise
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取Excel文件信息
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            文件信息字典
        """
        info = {
            'file_path': file_path,
            'file_exists': os.path.exists(file_path),
            'file_size': 0,
            'file_type': Path(file_path).suffix.lower(),
            'is_excel': self.is_excel_file(file_path),
            'available_libraries': self.available_libraries,
            'recommended_library': None,
            'sheets_info': []
        }
        
        if info['file_exists']:
            info['file_size'] = os.path.getsize(file_path)
            
            # 推荐处理库
            if info['file_type'] in ['.xlsx', '.xlsm'] and self.available_libraries.get('openpyxl'):
                info['recommended_library'] = 'openpyxl'
            elif info['file_type'] == '.xls' and self.available_libraries.get('xlrd'):
                info['recommended_library'] = 'xlrd'
            elif self.available_libraries.get('pandas'):
                info['recommended_library'] = 'pandas'
            
            # 获取工作表信息
            if info['is_excel']:
                try:
                    info['sheets_info'] = self._get_sheets_info(file_path)
                except Exception as e:
                    logger.warning(f"获取工作表信息失败: {e}")
        
        return info
    
    def _get_sheets_info(self, file_path: str) -> List[Dict[str, Any]]:
        """获取工作表信息"""
        sheets_info = []
        
        try:
            if self.available_libraries.get('pandas'):
                import pandas as pd
                excel_file = pd.ExcelFile(file_path)
                
                for sheet_name in excel_file.sheet_names:
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                        sheets_info.append({
                            'name': sheet_name,
                            'rows': len(df),
                            'columns': len(df.columns),
                            'has_data': not df.empty
                        })
                    except Exception as e:
                        sheets_info.append({
                            'name': sheet_name,
                            'error': str(e)
                        })
        except Exception as e:
            logger.warning(f"获取工作表信息失败: {e}")
        
        return sheets_info
