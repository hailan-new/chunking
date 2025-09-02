#!/usr/bin/env python3
"""
WPS原生处理器
使用WPS官方API和原生方案处理WPS文档
"""

import os
import logging
import requests
import tempfile
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class WPSNativeProcessor:
    """WPS原生文档处理器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化WPS原生处理器
        
        Args:
            api_key: WPS开放平台API密钥
        """
        self.api_key = api_key
        self.wps_api_base = "https://solution.wps.cn/api/v1"
        
    def convert_wps_to_docx(self, wps_file_path: str, output_dir: str) -> Optional[str]:
        """
        使用WPS原生方案将WPS文件转换为DOCX
        
        Args:
            wps_file_path: WPS文件路径
            output_dir: 输出目录
            
        Returns:
            转换后的DOCX文件路径，失败返回None
        """
        # 尝试多种WPS原生方案
        methods = [
            self._try_wps_api_conversion,
            self._try_wps_command_line,
            self._try_wps_com_interface,
            self._try_alternative_libraries
        ]
        
        for method in methods:
            try:
                result = method(wps_file_path, output_dir)
                if result:
                    logger.info(f"WPS原生转换成功: {method.__name__}")
                    return result
            except Exception as e:
                logger.warning(f"WPS原生方案 {method.__name__} 失败: {e}")
                continue
        
        logger.error("所有WPS原生方案都失败")
        return None
    
    def _try_wps_api_conversion(self, wps_file_path: str, output_dir: str) -> Optional[str]:
        """
        尝试使用WPS开放平台API转换
        
        Args:
            wps_file_path: WPS文件路径
            output_dir: 输出目录
            
        Returns:
            转换后的文件路径
        """
        if not self.api_key:
            logger.info("未提供WPS API密钥，跳过API转换")
            return None
        
        try:
            # 上传文件到WPS平台
            upload_url = f"{self.wps_api_base}/upload"
            
            with open(wps_file_path, 'rb') as f:
                files = {'file': f}
                headers = {'Authorization': f'Bearer {self.api_key}'}
                
                response = requests.post(upload_url, files=files, headers=headers, timeout=60)
                
                if response.status_code == 200:
                    upload_result = response.json()
                    file_id = upload_result.get('file_id')
                    
                    if file_id:
                        # 请求转换
                        convert_url = f"{self.wps_api_base}/convert"
                        convert_data = {
                            'file_id': file_id,
                            'target_format': 'docx'
                        }
                        
                        convert_response = requests.post(
                            convert_url, 
                            json=convert_data, 
                            headers=headers, 
                            timeout=120
                        )
                        
                        if convert_response.status_code == 200:
                            convert_result = convert_response.json()
                            download_url = convert_result.get('download_url')
                            
                            if download_url:
                                # 下载转换后的文件
                                output_file = os.path.join(
                                    output_dir, 
                                    f"{Path(wps_file_path).stem}_wps_api.docx"
                                )
                                
                                download_response = requests.get(download_url, timeout=60)
                                if download_response.status_code == 200:
                                    with open(output_file, 'wb') as f:
                                        f.write(download_response.content)
                                    
                                    logger.info(f"WPS API转换成功: {output_file}")
                                    return output_file
            
            logger.warning("WPS API转换失败")
            return None
            
        except Exception as e:
            logger.warning(f"WPS API转换异常: {e}")
            return None
    
    def _try_wps_command_line(self, wps_file_path: str, output_dir: str) -> Optional[str]:
        """
        尝试使用WPS命令行工具转换
        
        Args:
            wps_file_path: WPS文件路径
            output_dir: 输出目录
            
        Returns:
            转换后的文件路径
        """
        try:
            # 检查是否有WPS命令行工具
            wps_commands = ['wps', 'wpsoffice', 'kingsoft-office']
            
            for cmd in wps_commands:
                try:
                    # 检查命令是否存在
                    result = subprocess.run(['which', cmd], capture_output=True, text=True)
                    if result.returncode == 0:
                        wps_cmd = cmd
                        break
                except:
                    continue
            else:
                logger.info("未找到WPS命令行工具")
                return None
            
            # 使用WPS命令行转换
            output_file = os.path.join(
                output_dir, 
                f"{Path(wps_file_path).stem}_wps_cmd.docx"
            )
            
            cmd = [
                wps_cmd, '--headless', '--convert-to', 'docx',
                '--outdir', output_dir, wps_file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_file):
                logger.info(f"WPS命令行转换成功: {output_file}")
                return output_file
            
            logger.warning(f"WPS命令行转换失败: {result.stderr}")
            return None
            
        except Exception as e:
            logger.warning(f"WPS命令行转换异常: {e}")
            return None
    
    def _try_wps_com_interface(self, wps_file_path: str, output_dir: str) -> Optional[str]:
        """
        尝试使用WPS COM接口转换（Windows）
        
        Args:
            wps_file_path: WPS文件路径
            output_dir: 输出目录
            
        Returns:
            转换后的文件路径
        """
        try:
            import platform
            if platform.system() != 'Windows':
                logger.info("非Windows系统，跳过COM接口")
                return None
            
            try:
                import win32com.client
            except ImportError:
                logger.info("未安装pywin32，跳过COM接口")
                return None
            
            # 使用WPS COM接口
            wps_app = win32com.client.Dispatch("WPS.Application")
            wps_app.Visible = False
            
            # 打开WPS文档
            doc = wps_app.Documents.Open(os.path.abspath(wps_file_path))
            
            # 另存为DOCX
            output_file = os.path.join(
                output_dir, 
                f"{Path(wps_file_path).stem}_wps_com.docx"
            )
            
            # WPS的DOCX格式代码
            doc.SaveAs2(os.path.abspath(output_file), FileFormat=16)  # 16 = docx
            
            doc.Close()
            wps_app.Quit()
            
            if os.path.exists(output_file):
                logger.info(f"WPS COM接口转换成功: {output_file}")
                return output_file
            
            return None
            
        except Exception as e:
            logger.warning(f"WPS COM接口转换异常: {e}")
            return None
    
    def _try_alternative_libraries(self, wps_file_path: str, output_dir: str) -> Optional[str]:
        """
        尝试使用其他专门处理WPS格式的库
        
        Args:
            wps_file_path: WPS文件路径
            output_dir: 输出目录
            
        Returns:
            转换后的文件路径
        """
        try:
            # 尝试使用python-docx2txt（如果支持WPS）
            try:
                import docx2txt
                
                # 尝试直接读取WPS文件
                text = docx2txt.process(wps_file_path)
                
                if text and len(text) > 100:
                    # 创建一个简单的DOCX文件
                    from docx import Document
                    
                    doc = Document()
                    doc.add_paragraph(text)
                    
                    output_file = os.path.join(
                        output_dir, 
                        f"{Path(wps_file_path).stem}_docx2txt.docx"
                    )
                    
                    doc.save(output_file)
                    
                    logger.info(f"docx2txt转换成功: {output_file}")
                    return output_file
                    
            except ImportError:
                logger.info("未安装docx2txt")
            except Exception as e:
                logger.warning(f"docx2txt转换失败: {e}")
            
            # 可以在这里添加其他库的尝试
            
            return None
            
        except Exception as e:
            logger.warning(f"替代库转换异常: {e}")
            return None
