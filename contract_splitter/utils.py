"""
Utility functions for document processing, token counting, and text splitting.
"""

import re
from typing import List, Union, Optional
import logging

logger = logging.getLogger(__name__)


def count_tokens(text: str, method: str = "character") -> int:
    """
    Count tokens in text using specified method.
    
    Args:
        text: Input text
        method: Counting method ("character" or "tiktoken")
        
    Returns:
        Number of tokens
    """
    if method == "character":
        return len(text)
    elif method == "tiktoken":
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
            return len(encoding.encode(text))
        except ImportError:
            logger.warning("tiktoken not available, falling back to character count")
            return len(text)
    else:
        raise ValueError(f"Unsupported token counting method: {method}")


def split_chinese_sentences(text: str) -> List[str]:
    """
    Split Chinese text into sentences using Chinese punctuation.
    
    Args:
        text: Input Chinese text
        
    Returns:
        List of sentences
    """
    # Chinese sentence endings: 。！？；
    # Also include English punctuation for mixed content
    sentence_pattern = r'[。！？；.!?;]\s*'
    sentences = re.split(sentence_pattern, text)
    
    # Remove empty sentences and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def split_by_natural_breakpoints(text: str, max_tokens: int, 
                                token_counter: str = "character") -> List[str]:
    """
    Split text by natural breakpoints (sentences, paragraphs).
    
    Args:
        text: Input text
        max_tokens: Maximum tokens per chunk
        token_counter: Token counting method
        
    Returns:
        List of text chunks
    """
    chunks = []
    
    # First try to split by paragraphs
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        if count_tokens(paragraph, token_counter) <= max_tokens:
            chunks.append(paragraph)
        else:
            # Split paragraph by sentences
            sentences = split_chinese_sentences(paragraph)
            current_chunk = ""
            
            for sentence in sentences:
                test_chunk = f"{current_chunk} {sentence}".strip()
                
                if count_tokens(test_chunk, token_counter) <= max_tokens:
                    current_chunk = test_chunk
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
                    
                    # If single sentence is too long, force split
                    if count_tokens(current_chunk, token_counter) > max_tokens:
                        force_chunks = force_split_text(current_chunk, max_tokens, token_counter)
                        chunks.extend(force_chunks[:-1])
                        current_chunk = force_chunks[-1] if force_chunks else ""
            
            if current_chunk:
                chunks.append(current_chunk)
    
    return chunks


def force_split_text(text: str, max_tokens: int, 
                    token_counter: str = "character") -> List[str]:
    """
    Force split text when no natural breakpoints are available.
    
    Args:
        text: Input text
        max_tokens: Maximum tokens per chunk
        token_counter: Token counting method
        
    Returns:
        List of text chunks
    """
    chunks = []
    
    if token_counter == "character":
        # Simple character-based splitting
        for i in range(0, len(text), max_tokens):
            chunks.append(text[i:i + max_tokens])
    else:
        # Token-based splitting (more complex)
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            
            for i in range(0, len(tokens), max_tokens):
                chunk_tokens = tokens[i:i + max_tokens]
                chunk_text = encoding.decode(chunk_tokens)
                chunks.append(chunk_text)
        except ImportError:
            # Fallback to character splitting
            for i in range(0, len(text), max_tokens):
                chunks.append(text[i:i + max_tokens])
    
    return chunks


def sliding_window_split(text: str, max_tokens: int, overlap: int,
                        by_sentence: bool = True,
                        token_counter: str = "character") -> List[str]:
    """
    Split text using sliding window with overlap, respecting document structure.

    Args:
        text: Input text
        max_tokens: Maximum tokens per chunk
        overlap: Overlap length (in tokens or characters)
        by_sentence: Whether to respect sentence boundaries
        token_counter: Token counting method

    Returns:
        List of overlapping text chunks
    """
    if count_tokens(text, token_counter) <= max_tokens:
        return [text]

    # First, try structure-aware splitting for documents with clear hierarchy
    if _has_document_structure(text):
        return _structure_aware_split(text, max_tokens, overlap, token_counter)

    chunks = []

    if by_sentence:
        # Split by natural breakpoints first
        natural_chunks = split_by_natural_breakpoints(text, max_tokens, token_counter)

        # Apply sliding window with overlap
        for i, chunk in enumerate(natural_chunks):
            if i == 0:
                chunks.append(chunk)
            else:
                # Calculate overlap with previous chunk
                prev_chunk = chunks[-1]

                # Try to find overlap at sentence level
                prev_sentences = split_chinese_sentences(prev_chunk)
                curr_sentences = split_chinese_sentences(chunk)

                # Take last few sentences from previous chunk as overlap
                overlap_sentences = []
                overlap_tokens = 0

                for sentence in reversed(prev_sentences):
                    test_overlap = " ".join([sentence] + overlap_sentences)
                    if count_tokens(test_overlap, token_counter) <= overlap:
                        overlap_sentences.insert(0, sentence)
                        overlap_tokens = count_tokens(test_overlap, token_counter)
                    else:
                        break

                # Combine overlap with current chunk
                if overlap_sentences:
                    overlapped_chunk = " ".join(overlap_sentences + curr_sentences)
                    chunks.append(overlapped_chunk)
                else:
                    chunks.append(chunk)
    else:
        # Simple sliding window without sentence boundaries
        step_size = max_tokens - overlap
        
        if token_counter == "character":
            for i in range(0, len(text), step_size):
                chunk = text[i:i + max_tokens]
                chunks.append(chunk)
        else:
            try:
                import tiktoken
                encoding = tiktoken.get_encoding("cl100k_base")
                tokens = encoding.encode(text)
                
                for i in range(0, len(tokens), step_size):
                    chunk_tokens = tokens[i:i + max_tokens]
                    chunk_text = encoding.decode(chunk_tokens)
                    chunks.append(chunk_text)
            except ImportError:
                # Fallback to character-based
                for i in range(0, len(text), step_size):
                    chunk = text[i:i + max_tokens]
                    chunks.append(chunk)
    
    return chunks


def _has_document_structure(text: str) -> bool:
    """
    检查文本是否包含明显的文档结构标记

    Args:
        text: 要检查的文本

    Returns:
        True if text has clear document structure
    """
    structure_patterns = [
        '一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、', '九、', '十、',
        '（一）', '（二）', '（三）', '（四）', '（五）',
        '1、', '2、', '3、', '4、', '5、'
    ]

    # 检查是否包含多个结构标记
    found_patterns = sum(1 for pattern in structure_patterns if pattern in text)
    return found_patterns >= 3  # 至少包含3个结构标记


def _structure_aware_split(text: str, max_tokens: int, overlap: int, token_counter: str) -> List[str]:
    """
    结构感知的文本分割，尊重文档层次结构

    Args:
        text: 输入文本
        max_tokens: 每个chunk的最大token数
        overlap: 重叠长度
        token_counter: token计数方法

    Returns:
        分割后的chunks列表
    """
    # 按结构标记分割文本
    sections = _split_by_structure_markers(text)

    if not sections:
        # 如果没有找到结构标记，回退到普通分割
        return _simple_sliding_window_split(text, max_tokens, overlap, token_counter)

    chunks = []
    current_chunk = ""

    for section in sections:
        section_tokens = count_tokens(section, token_counter)
        current_tokens = count_tokens(current_chunk, token_counter)

        # 如果添加这个section会超过限制
        if current_tokens + section_tokens > max_tokens and current_chunk:
            # 保存当前chunk
            chunks.append(current_chunk.strip())

            # 开始新的chunk，可能包含一些重叠内容
            if overlap > 0 and chunks:
                # 从当前chunk的末尾取一些内容作为重叠
                overlap_content = _get_overlap_content(current_chunk, overlap, token_counter)
                current_chunk = overlap_content + " " + section if overlap_content else section
            else:
                current_chunk = section
        else:
            # 添加到当前chunk
            if current_chunk:
                current_chunk += " " + section
            else:
                current_chunk = section

    # 添加最后的chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def _split_by_structure_markers(text: str) -> List[str]:
    """
    按结构标记分割文本

    Args:
        text: 输入文本

    Returns:
        分割后的段落列表
    """
    import re

    # 定义结构标记模式
    patterns = [
        r'(一、[^一二三四五六七八九十]*?)(?=二、|三、|四、|五、|六、|七、|八、|九、|十、|$)',
        r'(二、[^一二三四五六七八九十]*?)(?=一、|三、|四、|五、|六、|七、|八、|九、|十、|$)',
        r'(三、[^一二三四五六七八九十]*?)(?=一、|二、|四、|五、|六、|七、|八、|九、|十、|$)',
        r'(四、[^一二三四五六七八九十]*?)(?=一、|二、|三、|五、|六、|七、|八、|九、|十、|$)',
        r'(五、[^一二三四五六七八九十]*?)(?=一、|二、|三、|四、|六、|七、|八、|九、|十、|$)',
        r'(六、[^一二三四五六七八九十]*?)(?=一、|二、|三、|四、|五、|七、|八、|九、|十、|$)',
        r'(七、[^一二三四五六七八九十]*?)(?=一、|二、|三、|四、|五、|六、|八、|九、|十、|$)',
        r'(八、[^一二三四五六七八九十]*?)(?=一、|二、|三、|四、|五、|六、|七、|九、|十、|$)',
    ]

    # 简单的分割方法：按常见的层次标记分割
    sections = []
    remaining_text = text

    # 按主要标记分割
    for marker in ['一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、']:
        if marker in remaining_text:
            parts = remaining_text.split(marker)
            if len(parts) > 1:
                # 第一部分（如果不为空）
                if parts[0].strip():
                    sections.append(parts[0].strip())

                # 后续部分，每部分前加上标记
                for i, part in enumerate(parts[1:], 1):
                    if part.strip():
                        if i == len(parts) - 1:  # 最后一部分
                            sections.append(f"{marker}{part.strip()}")
                        else:
                            # 找到下一个标记的位置
                            next_marker_pos = -1
                            for next_marker in ['一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、']:
                                if next_marker != marker and next_marker in part:
                                    pos = part.find(next_marker)
                                    if next_marker_pos == -1 or pos < next_marker_pos:
                                        next_marker_pos = pos

                            if next_marker_pos != -1:
                                sections.append(f"{marker}{part[:next_marker_pos].strip()}")
                                remaining_text = part[next_marker_pos:]
                            else:
                                sections.append(f"{marker}{part.strip()}")
                break

    # 如果没有成功分割，按段落分割
    if not sections:
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        sections = paragraphs

    return sections


def _get_overlap_content(text: str, overlap: int, token_counter: str) -> str:
    """
    从文本末尾获取重叠内容

    Args:
        text: 源文本
        overlap: 重叠长度
        token_counter: token计数方法

    Returns:
        重叠内容
    """
    if count_tokens(text, token_counter) <= overlap:
        return text

    # 按句子分割，从末尾取句子直到达到重叠长度
    sentences = split_chinese_sentences(text)
    overlap_sentences = []
    overlap_tokens = 0

    for sentence in reversed(sentences):
        test_overlap = " ".join([sentence] + overlap_sentences)
        test_tokens = count_tokens(test_overlap, token_counter)

        if test_tokens <= overlap:
            overlap_sentences.insert(0, sentence)
            overlap_tokens = test_tokens
        else:
            break

    return " ".join(overlap_sentences)


def _simple_sliding_window_split(text: str, max_tokens: int, overlap: int, token_counter: str) -> List[str]:
    """
    简单的滑动窗口分割（回退方法）

    Args:
        text: 输入文本
        max_tokens: 每个chunk的最大token数
        overlap: 重叠长度
        token_counter: token计数方法

    Returns:
        分割后的chunks列表
    """
    chunks = []
    step_size = max_tokens - overlap

    if token_counter == "character":
        for i in range(0, len(text), step_size):
            chunk = text[i:i + max_tokens]
            chunks.append(chunk)
    else:
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)

            for i in range(0, len(tokens), step_size):
                chunk_tokens = tokens[i:i + max_tokens]
                chunk_text = encoding.decode(chunk_tokens)
                chunks.append(chunk_text)
        except ImportError:
            # Fallback to character-based splitting
            for i in range(0, len(text), step_size):
                chunk = text[i:i + max_tokens]
                chunks.append(chunk)

    return chunks


def clean_text(text: str) -> str:
    """
    Clean text by removing unnecessary spaces between characters while preserving line breaks.

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Split by lines to preserve line breaks
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # Remove extra spaces within each line (but not line breaks)
        line = re.sub(r'[ \t]+', ' ', line)  # Multiple spaces/tabs to single space

        # Remove spaces around Chinese punctuation
        line = re.sub(r'\s*([，。；：！？、）】}])\s*', r'\1', line)
        line = re.sub(r'\s*([（【{])\s*', r'\1', line)

        # Remove spaces around numbers and Chinese characters
        line = re.sub(r'(\d)\s+([一二三四五六七八九十])', r'\1\2', line)
        line = re.sub(r'([一二三四五六七八九十])\s+(\d)', r'\1\2', line)

        # Remove spaces between Chinese characters (but keep spaces around English/numbers)
        line = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', line)

        # Remove leading/trailing whitespace from each line
        line = line.strip()

        cleaned_lines.append(line)

    # Rejoin with original line breaks
    return '\n'.join(cleaned_lines)


def detect_heading_level(text: str) -> int:
    """
    Detect heading level based on text patterns.
    
    Args:
        text: Heading text
        
    Returns:
        Heading level (1-6)
    """
    text = text.strip()
    
    # Chinese chapter/section patterns
    if re.match(r'^第[一二三四五六七八九十\d]+章', text):
        return 1  # Chapter
    elif re.match(r'^第[一二三四五六七八九十\d]+节', text):
        return 2  # Section
    elif re.match(r'^[一二三四五六七八九十]+[、．.]', text) or re.match(r'^\d+[、．]', text):
        return 3  # Numbered item
    elif re.match(r'^（[一二三四五六七八九十\d]+）', text):
        return 4  # Parenthetical item
    
    # English patterns
    elif re.match(r'^Chapter\s+\d+', text, re.IGNORECASE):
        return 1
    elif re.match(r'^Section\s+\d+', text, re.IGNORECASE):
        return 2
    elif re.match(r'^\d+\.\d+', text):
        return 4
    elif re.match(r'^\d+\.\s', text):
        return 3
    
    # Default
    return 3
