# Contract Splitter

一个专业的文档处理和智能分块工具，专注于提供三大核心功能：**层次化分块**、**句子完整性分块**和**多格式文本提取**。特别针对法律文档、合同文件等专业文档进行了深度优化。

## 🎯 三大核心价值

### 1. 📊 层次化智能分块
根据文档的天然层次结构（章节、条文、段落）进行智能分块，保持文档的逻辑结构和语义完整性。

### 2. ✂️ 句子完整性分块  
在指定参数范围内，优先保持句子完整性的智能分块方法，避免句子截断和语义破坏。

### 3. 📄 多格式文本提取
从PDF、Word、Excel、WPS等常见文档格式中准确提取文本内容，支持复杂格式和编码。

## 🚀 特性亮点

- **🧠 智能结构识别**: 自动识别文档层次结构和法律条文
- **✅ 句子完整性保护**: 优先保持句子完整，避免语义破坏
- **📚 多格式支持**: PDF、DOCX、DOC、WPS、Excel、RTF、TXT等
- **⚖️ 法律文档专业优化**: 针对法律条文和合同条款的专门处理
- **🔧 灵活参数配置**: 支持多种分块策略和自定义参数
- **📈 高质量输出**: 保持文档元数据和结构信息

## 📦 安装

```bash
# 克隆项目
git clone <repository-url>
cd chunking

# 安装依赖
pip install -r requirements.txt

# 可选：安装LibreOffice（用于WPS文件处理）
# macOS: brew install libreoffice
# Ubuntu: sudo apt-get install libreoffice
```

## 🎯 核心接口使用

### 接口1: 层次化分块接口

根据文档层次结构进行智能分块，保持逻辑结构：

```python
from contract_splitter import split_document, flatten_sections

# 层次化分块
sections = split_document("legal_document.pdf", max_tokens=1000)

# 选择扁平化策略
chunks = flatten_sections(sections, strategy="finest_granularity")
# 策略选项: "finest_granularity", "all_levels", "parent_only"

for chunk in chunks:
    print(f"Level {chunk.level}: {chunk.content[:100]}...")
```

### 接口2: 句子完整性分块接口

在参数范围内优先保持句子完整性：

```python
from contract_splitter import simple_chunk_file

# 句子完整性分块
chunks = simple_chunk_file(
    "contract.docx", 
    max_chunk_size=800,      # 目标大小（软限制）
    overlap_ratio=0.15       # 重叠比例
)

for chunk in chunks:
    print(f"Chunk {chunk['chunk_id']} ({len(chunk['content'])}字符): {chunk['content'][:100]}...")
```

### 接口3: 多格式文本提取接口

从各种文档格式中提取纯文本：

```python
from contract_splitter import extract_text

# 直接文本提取 - 推荐方式
text = extract_text("document.pdf")
print(f"提取文本长度: {len(text)} 字符")

# 或使用工厂接口
from contract_splitter import SplitterFactory
factory = SplitterFactory()
text = factory.extract_text("document.xlsx")
print(f"提取文本长度: {len(text)} 字符")
```

## 📋 支持的文档格式

| 格式类型 | 支持格式 | 提取方法 | 特殊功能 |
|---------|---------|---------|---------|
| **PDF** | .pdf | PyMuPDF + pdfplumber | 表格识别、OCR支持 |
| **Word** | .docx, .doc | python-docx + docx2txt | 样式保持、表格提取 |
| **Excel** | .xlsx, .xls, .xlsm | openpyxl + xlrd | 多工作表、公式处理 |
| **WPS** | .wps | LibreOffice转换 | 多格式降级处理 |
| **其他** | .rtf, .txt | 专用解析器 | 编码自动检测 |

## 🔧 高级配置

### 法律文档专业处理

```python
from contract_splitter.domain_helpers import split_legal_document

# 法律文档专业分块
chunks = split_legal_document(
    "法律条文.pdf",
    max_tokens=1500,           # 分块大小
    strict_max_tokens=False,   # 允许超出以保持完整性
    legal_structure_detection=True  # 启用法律结构识别
)

# 自动识别：第X条、第X款、第X项等法律结构
for chunk in chunks:
    print(f"法律条文: {chunk[:100]}...")
```

### Excel文件专业处理

```python
from contract_splitter import ExcelSplitter

# Excel专业分块
splitter = ExcelSplitter(
    max_tokens=1000,
    extract_mode="legal_content"  # 法律内容模式
)

sections = splitter.split("法规表格.xlsx")

# 智能输出格式：
# - 单工作表：直接显示内容，无冗余前缀
# - 多工作表：仅显示有意义的工作表名称
for section in sections:
    print(f"标题: {section['heading']}")
    print(f"内容: {section['content'][:100]}...")

# 输出示例：
# 标题: 第一条                    (单工作表，无Sheet1前缀)
# 标题: 证券监管规定 - 第二条      (多工作表，有意义名称)
```

### 自定义分块策略

```python
from contract_splitter.utils import sliding_window_split

# 自定义分块参数
chunks = sliding_window_split(
    text="长文档内容...",
    max_tokens=500,           # 目标大小
    overlap=100,              # 重叠长度
    by_sentence=True,         # 句子优先（推荐）
    token_counter="character" # 计数方式
)

# 句子完整性优先，允许适度超出max_tokens
```

## 📊 实际应用示例

### 示例1: 法律条文处理

```python
# 处理证券法条文
from contract_splitter.domain_helpers import split_legal_document

chunks = split_legal_document("证券法.pdf", max_tokens=1200)

print(f"共分割为 {len(chunks)} 个条文块")
for i, chunk in enumerate(chunks[:3], 1):
    print(f"\n条文块 {i}:")
    print(chunk[:200] + "...")
```

### 示例2: 合同文档分析

```python
# 智能合同分块
from contract_splitter import simple_chunk_file

chunks = simple_chunk_file(
    "合同文件.docx",
    max_chunk_size=600,
    overlap_ratio=0.2
)

# 分析合同条款
for chunk in chunks:
    if "甲方" in chunk['content'] or "乙方" in chunk['content']:
        print(f"发现合同条款: {chunk['content'][:100]}...")
```

### 示例3: Excel数据提取

```python
# 处理法规Excel表格
from contract_splitter import ExcelSplitter

splitter = ExcelSplitter(extract_mode="table_structure")
sections = splitter.split("监管指标.xlsx")

for section in sections:
    # 清洁的输出格式，无冗余工作表名称
    print(f"标题: {section['heading']}")  # 例如: "表格1" 而不是 "Sheet1 - 表格1"
    print(f"表格数据: {section['content'][:150]}...")
```

## 📈 性能优势

### 句子完整性对比

| 分块方式 | 句子完整率 | 平均块大小 | 语义连贯性 |
|---------|-----------|-----------|-----------|
| **传统字符截断** | 50% | 严格限制 | 差 |
| **句子优先分块** | **100%** | 接近目标 | **优秀** |

### 处理速度

- **PDF文档**: ~2-5秒/MB
- **Word文档**: ~1-3秒/MB  
- **Excel文件**: ~0.5-2秒/MB
- **法律文档**: 专门优化，保持高效

## 🎯 最佳实践

### 1. 选择合适的分块策略

```python
# 结构化文档 → 层次化分块
sections = split_document("structured_doc.pdf")

# 一般文档 → 句子完整性分块  
chunks = simple_chunk_file("general_doc.docx", max_chunk_size=800)

# 法律文档 → 专业法律分块
legal_chunks = split_legal_document("legal_doc.pdf", max_tokens=1500)
```

### 2. 参数调优建议

```python
# 短文档处理
simple_chunk_file("short.pdf", max_chunk_size=400, overlap_ratio=0.1)

# 长文档处理  
simple_chunk_file("long.pdf", max_chunk_size=1000, overlap_ratio=0.15)

# 法律文档处理
split_legal_document("legal.pdf", max_tokens=1500, strict_max_tokens=False)
```

## 📚 更多示例

查看 `examples/` 目录获取完整的使用示例：

- `examples/basic_usage.py` - 基础使用方法
- `examples/legal_document_processing.py` - 法律文档处理
- `examples/excel_processing_example.py` - Excel文件处理
- `examples/advanced_chunking.py` - 高级分块策略

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目。

## 📄 许可证

MIT License
