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
    Split text using sliding window with overlap.
    
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


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


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
