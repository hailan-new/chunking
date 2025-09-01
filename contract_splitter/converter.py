"""
Document converter module for automatic .doc to .docx conversion.
"""

import os
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


class DocumentConverter:
    """
    Handles automatic conversion of legacy document formats to modern formats.
    
    Supports multiple conversion methods with automatic fallbacks.
    """
    
    def __init__(self, cleanup_temp_files: bool = True):
        """
        Initialize the document converter.
        
        Args:
            cleanup_temp_files: Whether to automatically clean up temporary files
        """
        self.cleanup_temp_files = cleanup_temp_files
        self.temp_files = []  # Track temporary files for cleanup
    
    def convert_to_docx(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert a .doc file to .docx format using available methods.
        
        Args:
            file_path: Path to the input .doc file
            output_path: Optional output path. If None, creates temporary file
            
        Returns:
            Path to the converted .docx file
            
        Raises:
            ValueError: If conversion fails with all available methods
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        if file_path.suffix.lower() not in ['.doc']:
            raise ValueError(f"Input file must be .doc format, got: {file_path.suffix}")
        
        # Determine output path
        if output_path is None:
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            output_path = Path(temp_dir) / f"{file_path.stem}.docx"
            self.temp_files.append(str(output_path))
            self.temp_files.append(temp_dir)
        else:
            output_path = Path(output_path)
        
        # Try conversion methods in order of preference
        conversion_methods = [
            self._convert_with_libreoffice,
            self._convert_with_win32com,
            self._convert_with_pandoc,
            self._convert_with_unoconv,
        ]
        
        last_error = None
        
        for method in conversion_methods:
            try:
                logger.info(f"Trying conversion method: {method.__name__}")
                result_path = method(str(file_path), str(output_path))
                
                if result_path and Path(result_path).exists():
                    logger.info(f"✓ Conversion successful with {method.__name__}")
                    return str(result_path)
                    
            except Exception as e:
                logger.warning(f"✗ {method.__name__} failed: {e}")
                last_error = e
                continue
        
        # All methods failed
        raise ValueError(f"Failed to convert {file_path} to .docx format. "
                        f"Last error: {last_error}. "
                        f"Consider installing LibreOffice, pandoc, or using Windows with Office.")
    
    def _convert_with_libreoffice(self, input_path: str, output_path: str) -> str:
        """Convert using LibreOffice headless mode."""
        import subprocess
        
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # LibreOffice command (try both libreoffice and soffice)
        libreoffice_commands = ['libreoffice', 'soffice']
        cmd = None

        for lo_cmd in libreoffice_commands:
            try:
                # Test if command exists
                import subprocess
                subprocess.run([lo_cmd, '--version'],
                              capture_output=True, check=True, timeout=5)
                cmd = [
                    lo_cmd,
                    '--headless',
                    '--convert-to', 'docx',
                    '--outdir', str(output_dir),
                    input_path
                ]
                break
            except:
                continue

        if cmd is None:
            raise ValueError("LibreOffice not found. Install with: brew install libreoffice (Mac) or apt-get install libreoffice (Linux)")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60  # 60 second timeout
            )
            
            # LibreOffice creates file with same name but .docx extension
            expected_output = output_dir / f"{Path(input_path).stem}.docx"
            
            if expected_output.exists():
                # Move to desired output path if different
                if str(expected_output) != output_path:
                    shutil.move(str(expected_output), output_path)
                return output_path
            else:
                raise ValueError("LibreOffice conversion completed but output file not found")
                
        except FileNotFoundError:
            raise ValueError("LibreOffice not found. Install with: brew install libreoffice (Mac) or apt-get install libreoffice (Linux)")
        except subprocess.TimeoutExpired:
            raise ValueError("LibreOffice conversion timed out")
        except subprocess.CalledProcessError as e:
            raise ValueError(f"LibreOffice conversion failed: {e.stderr}")
    
    def _convert_with_win32com(self, input_path: str, output_path: str) -> str:
        """Convert using Windows COM automation (Windows only)."""
        if os.name != 'nt':
            raise ValueError("win32com only available on Windows")
        
        try:
            import win32com.client
        except ImportError:
            raise ValueError("win32com not available. Install with: pip install pywin32")
        
        # Ensure absolute paths
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)
        
        # Create output directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        word = None
        doc = None
        
        try:
            # Create Word application
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False
            
            # Open document
            doc = word.Documents.Open(input_path)
            
            # Save as .docx (format code 16 = docx)
            doc.SaveAs2(output_path, FileFormat=16)
            
            return output_path
            
        except Exception as e:
            raise ValueError(f"Word COM automation failed: {e}")
        finally:
            # Clean up
            if doc:
                try:
                    doc.Close()
                except:
                    pass
            if word:
                try:
                    word.Quit()
                except:
                    pass
    
    def _convert_with_pandoc(self, input_path: str, output_path: str) -> str:
        """Convert using pandoc."""
        import subprocess
        
        # Create output directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'pandoc',
            input_path,
            '-f', 'doc',
            '-t', 'docx',
            '-o', output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
            
            if Path(output_path).exists():
                return output_path
            else:
                raise ValueError("Pandoc conversion completed but output file not found")
                
        except FileNotFoundError:
            raise ValueError("Pandoc not found. Install from https://pandoc.org/")
        except subprocess.TimeoutExpired:
            raise ValueError("Pandoc conversion timed out")
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Pandoc conversion failed: {e.stderr}")
    
    def _convert_with_unoconv(self, input_path: str, output_path: str) -> str:
        """Convert using unoconv (LibreOffice backend)."""
        import subprocess
        
        # Create output directory
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'unoconv',
            '-f', 'docx',
            '-o', output_path,
            input_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
            
            if Path(output_path).exists():
                return output_path
            else:
                raise ValueError("unoconv conversion completed but output file not found")
                
        except FileNotFoundError:
            raise ValueError("unoconv not found. Install with: pip install unoconv")
        except subprocess.TimeoutExpired:
            raise ValueError("unoconv conversion timed out")
        except subprocess.CalledProcessError as e:
            raise ValueError(f"unoconv conversion failed: {e.stderr}")
    
    def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                if os.path.isfile(temp_file):
                    os.unlink(temp_file)
                elif os.path.isdir(temp_file):
                    shutil.rmtree(temp_file)
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_file}: {e}")
        
        self.temp_files.clear()
    
    def __del__(self):
        """Automatic cleanup on object destruction."""
        if self.cleanup_temp_files:
            self.cleanup()


def convert_doc_to_docx(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convenience function to convert a .doc file to .docx format.
    
    Args:
        input_path: Path to the input .doc file
        output_path: Optional output path. If None, creates temporary file
        
    Returns:
        Path to the converted .docx file
    """
    converter = DocumentConverter()
    return converter.convert_to_docx(input_path, output_path)


def is_conversion_available() -> dict:
    """
    Check which conversion methods are available on the current system.
    
    Returns:
        Dictionary with availability status of each conversion method
    """
    methods = {
        'libreoffice': False,
        'win32com': False,
        'pandoc': False,
        'unoconv': False
    }
    
    # Check LibreOffice (try both libreoffice and soffice commands)
    try:
        import subprocess
        libreoffice_commands = ['libreoffice', 'soffice']
        for cmd in libreoffice_commands:
            try:
                subprocess.run([cmd, '--version'],
                              capture_output=True, check=True, timeout=5)
                methods['libreoffice'] = True
                break
            except:
                continue
    except:
        pass
    
    # Check win32com (Windows only)
    if os.name == 'nt':
        try:
            import win32com.client
            methods['win32com'] = True
        except:
            pass
    
    # Check pandoc
    try:
        import subprocess
        subprocess.run(['pandoc', '--version'], 
                      capture_output=True, check=True, timeout=5)
        methods['pandoc'] = True
    except:
        pass
    
    # Check unoconv
    try:
        import subprocess
        subprocess.run(['unoconv', '--version'], 
                      capture_output=True, check=True, timeout=5)
        methods['unoconv'] = True
    except:
        pass
    
    return methods
