# Scripts 目录

本目录包含用于数据处理、清洗和转换的脚本工具。

## 目录结构

```
scripts/
├── check_encoding_type.py      # 检测文件编码类型
├── compute_ppl.py            # 计算文本PPL困惑度
├── convert_to_utf8.py        # 编码转换为UTF-8
├── download_hf_dataset.py    # 下载HuggingFace数据集
├── filter_mongolian_traditional.py  # 传统蒙古文过滤
├── plaintext_to_jsonl.py      # 纯文本转换为JSONL
├── process_batch_config.py    # 批量处理配置文件
├── run_slurm.sh             # Slurm运行脚本
├── dlc/                    # 阿里云DLC容器运行脚本
│   ├── partition_data_dlc.py
│   └── run_on_dlc.sh
└── README.md               # 本文件
```

## 脚本功能说明

### 数据处理脚本

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| [`check_encoding_type.py`](check_encoding_type.py) | 检测文件编码类型 | `python check_encoding_type.py <file>` |
| [`convert_to_utf8.py`](convert_to_utf8.py) | 将文件转换为UTF-8编码 | `python convert_to_utf8.py <input> [-o output]` |
| [`plaintext_to_jsonl.py`](plaintext_to_jsonl.py) | 将txt文件转换为JSONL格式 | `python plaintext_to_jsonl.py <folder> [output]` |
| [`download_hf_dataset.py`](download_hf_dataset.py) | 下载HuggingFace数据集 | `python download_hf_dataset.py <dataset_name>` |

### 数据清洗脚本

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| [`filter_mongolian_traditional.py`](filter_mongolian_traditional.py) | 基于Unicode范围过滤传统蒙古文 | `python filter_mongolian_traditional.py <input> <field> <output> <threshold>` |
| [`compute_ppl.py`](compute_ppl.py) | 计算文本PPL困惑度 | 见下文详细说明 |

### 批处理脚本

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| [`process_batch_config.py`](process_batch_config.py) | 批量运行data-juicer配置 | `python process_batch_config.py --start N --end M --total T --filepath config.yaml` |
| [`run_slurm.sh`](run_slurm.sh) | Slurm集群运行脚本 | `bash run_slurm.sh` |

### DLC脚本

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| [`dlc/partition_data_dlc.py`](dlc/partition_data_dlc.py) | DLC数据分区 | `python dlc/partition_data_dlc.py` |
| [`dlc/run_on_dlc.sh`](dlc/run_on_dlc.sh) | 在DLC上运行 | `bash dlc/run_on_dlc.sh` |

---

## compute_ppl.py 详细说明

计算文本的PPL（Perplexity，困惑度），支持两种计算方式：

### 方式1: 使用 HuggingFace Transformers 模型

```bash
python compute_ppl.py input.jsonl -o output.jsonl
python compute_ppl.py input.jsonl -t text -m gpt2 -o output.jsonl
```

**参数说明：**
- `input`: 输入JSONL文件路径
- `-o, --output`: 输出JSONL文件路径 (默认: output_ppl.jsonl)
- `-t, --field`: 文本字段名 (默认: text)
- `-m, --method`: 计算方式 (默认: hf)
- `--model`: HuggingFace模型名称 (默认: gpt2)

### 方式2: 使用 data-juicer 内置算子

```bash
python compute_ppl.py input.jsonl -o output.jsonl --method dj
python compute_ppl.py input.jsonl -o output.jsonl --method dj --lang zh --min-ppl 0 --max-ppl 1500
```

**额外参数说明：**
- `--lang`: data-juicer语言代码 (默认: en)
- `--min-ppl`: 最小PPL阈值 (默认: 0)
- `--max-ppl`: 最大PPL阈值 (默认: 1500)

**支持的语言代码：** en, zh, fr, de, es, ru, ja, ar 等

---

## filter_mongolian_traditional.py 详细说明

专门用于过滤传统蒙古文（Traditional Mongolian）的脚本。由于 data-juicer 的 language_id_score_filter 只能识别西里尔蒙古语（Modern Mongolian），因此需要此脚本辅���。

```bash
python filter_mongolian_traditional.py <input.jsonl> <field_name> <output.jsonl> <threshold>
```

**参数说明：**
- `input.jsonl`: 输入JSONL文件路径
- `field_name`: 文本字段名（如 text, content 等）
- `output.jsonl`: 输出JSONL文件路径
- `threshold`: 蒙古文字符占比阈值 (0.0~1.0)

**示例：**
```bash
python filter_mongolian_traditional.py data.jsonl text mongolian.jsonl 0.7
```

这会保留蒙古文字符占比 ≥ 70% 的文本。

---

## 依赖安装

部分脚本需要额外依赖，请使用以下命令安装：

```bash
# 基础依赖
pip install py-data-juicer

# PPL计算依赖
pip install transformers torch

# 编码检测依赖
pip install chardet
```

---

## 注意事项

1. **路径问题**：脚本中使用的路径可能需要根据实际情况修改
2. **模型下载**：首次运行时会自动下载所需模型（可能需要较长时间）
3. **内存问题**：大文件处理时请注意内存占用，可以使用批处理方式
