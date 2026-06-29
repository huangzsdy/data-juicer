# Configs 目录

本目录包含用于 data-juicer 数据清洗管道的配置文件（YAML格式）。

## 目录结构

```
configs/
├── language_id_score_filter_config.yaml    # 语言识别过滤配置
├── label_studio_localhost_connection.json # Label Studio连接配置
└── README.md                              # 本文件
```

## 配置文件说明

### language_id_score_filter_config.yaml

语言识别过滤配置文件，使用 data-juicer 的 [`language_id_score_filter`](data_juicer/ops/filter/language_id_score_filter.py) 算子过滤特定语言的数据。

**功能：**
- 使用 FastText 模型识别文本语言
- 保留指定语言的样本
- 过滤置信度低于阈值的样本

**配置参数：**

| 参数 | 说明 | 示例值 |
|------|------|--------|
| `project_name` | 项目名称 | language_id_score_filter |
| `dataset_path` | 输入数据集路径 | ./data/input.jsonl |
| `export_path` | 输出数据集路径 | ./outputs/filtered.jsonl |
| `np` | 并行进程数 | 4 |
| `text_keys` | 文本字段名 | text |
| `process[].language_id_score_filter.lang` | 要保留的语言代码 | mn, zh, en |
| `process[].language_id_score_filter.min_score` | 最小置信度 | 0.8 |

**使用示例：**

```bash
# 运行配置
dj-process --config configs/language_id_score_filter_config.yaml
```

**支持的语言代码：**

| 代码 | 语言 |
|------|------|
| zh | 中文 |
| en | 英文 |
| mn | 蒙古语（西里尔） |
| fr | 法语 |
| de | 德语 |
| es | 西班牙语 |
| ru | 俄语 |
| ja | 日语 |
| ar | 阿拉伯语 |

---

### label_studio_localhost_connection.json

Label Studio 本地连接配置文件，用于与 Label Studio 标注平台集成。

**用途：**
- 配置本地 Label Studio 服务连接
- 用于数据标注和质量管理流程

**配置参数：**

| 参数 | 说明 |
|------|------|
| url | Label Studio 服务地址 |
| api_key | API 密钥 |
| project_id | 项目ID |

---

## 与 scripts 目录的区别

| 目录 | 用途 | 特点 |
|------|------|------|
| `scripts/` | Python 脚本工具 | 独立运行，需要手动执行 |
| `configs/` | data-juicer 配置文件 | 声明式配置，通过 dj-process 运行 |

**推荐使用流程：**

1. 使用 `configs/` 中的配置文件进行数据清洗（推荐）
2. 使用 `scripts/` 中的脚本进行辅助处理（如PPL计算、编码转换等）

---

## 依赖安装

```bash
# 安装 data-juicer
pip install py-data-juicer

# 运行配置
dj-process --config configs/language_id_score_filter_config.yaml
```

---

## 注意事项

1. **路径修改**：使用前需修改配置文件中的 `dataset_path` 为实际数据路径
2. **语言支持**：确保需要过滤的语言在 FastText 模型支持列表中
3. **阈值选择**：建议使用 0.8 作为最小置信度，过高可能过滤掉过多有效数据