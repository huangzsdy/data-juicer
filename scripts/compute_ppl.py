#!/usr/bin/env python3
"""
计算文本的PPL（Perplexity，困惑度）

支持两种计算方式：
1. 使用 HuggingFace Transformers 模型 (GPT/MLM)
2. 使用 data-juicer 内置的 perplexity_filter 算子 (KenLM + SentencePiece)
"""

import json
import math
import argparse
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, GPT2LMHeadModel, GPT2Tokenizer


# ==================== 方式1: 使用 HuggingFace Transformers ====================

def load_hf_model(model_name="gpt2"):
    """加载HuggingFace预训练语言模型"""
    print(f"正在加载HuggingFace模型: {model_name}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
    except Exception as e:
        print(f"加载模型失败: {e}, 将使用默认的gpt2模型")
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        model = GPT2LMHeadModel.from_pretrained("gpt2")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    model.eval()
    
    print(f"模型已加载，使用设备: {device}")
    return model, tokenizer, device


def compute_ppl_hf(model, tokenizer, text, device):
    """使用HuggingFace模型计算单个文本的PPL"""
    try:
        encodings = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        )
        
        input_ids = encodings.input_ids.to(device)
        attention_mask = encodings.attention_mask.to(device)
        
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            
            shift_logits = logits[:, :-1, :].contiguous()
            shift_labels = input_ids[:, 1:].contiguous()
            
            loss = torch.nn.functional.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                reduction="mean"
            )
            
            ppl = math.exp(loss.item())
        
        return ppl
        
    except Exception as e:
        print(f"计算PPL时出错: {e}")
        return float("inf")


def process_with_hf_model(model, tokenizer, input_path, text_field, output_path, device):
    """使用HuggingFace模型处理数据集"""
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"错误: 输入文件 '{input_path}' 不存在")
        return
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    total = 0
    ppl_sum = 0.0
    ppl_values = []
    
    with open(input_file, 'r', encoding='utf-8') as fin, \
         open(output_file, 'w', encoding='utf-8') as fout:
        
        for line_num, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"警告: 第 {line_num} 行不是有效JSON，跳过")
                continue
            
            text = data.get(text_field, "")
            if not isinstance(text, str) or not text:
                continue
            
            total += 1
            
            ppl = compute_ppl_hf(model, tokenizer, text, device)
            ppl_values.append(ppl)
            ppl_sum += ppl
            
            data["ppl"] = ppl
            data["ppl_method"] = "huggingface"
            
            fout.write(json.dumps(data, ensure_ascii=False) + "\n")
            
            if total % 100 == 0:
                avg_ppl = ppl_sum / total
                print(f"已处理 {total} 行，平均PPL: {avg_ppl:.2f}")
    
    if ppl_values:
        print_ppl_stats(ppl_values, total, output_file)


# ==================== 方式2: 使用 data-juicer ====================

def process_with_data_juicer(input_path, text_field, output_path, lang="en", min_ppl=0, max_ppl=1500, export_stats=True):
    """
    使用data-juicer的perplexity_filter算子计算PPL
    
    注意: data-juicer会将PPL作为stats保存，可以导出stats文件查看PPL值。
    默认导出stats到单独的文件。
    """
    import yaml
    from data_juicer.config import load_config, run
    
    # 构建输出路径
    output_dir = Path(output_path).parent
    stats_output_path = str(output_dir / "ppl_stats.jsonl")
    
    # 创建临时配置文件
    temp_config = {
        "project_name": "compute_ppl",
        "dataset_path": input_path,
        "export_path": output_path,
        "export_stats": export_stats,  # 导出stats
        "np": 4,
        "text_keys": text_field,
        "process": [
            {
                "perplexity_filter": {
                    "lang": lang,
                    "min_ppl": min_ppl,
                    "max_ppl": max_ppl
                }
            }
        ]
    }
    
    temp_yaml_path = Path("temp_ppl_config.yaml")
    with open(temp_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(temp_config, f, default_flow_style=False)
    
    print(f"正在使用data-juicer计算PPL (lang={lang})...")
    print(f"配置文件: {temp_yaml_path}")
    
    try:
        # 加载并运行配置
        cfg = load_config(str(temp_yaml_path))
        run(cfg)
        print(f"\n✅ data-juicer处理完成!")
        print(f"保留的样本: {output_path}")
        
        # 读取stats文件获取PPL统计
        if export_stats and Path(stats_output_path).exists():
            print(f"Stats文件: {stats_output_path}")
            ppl_values = []
            with open(stats_output_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        ppl = data.get("stats", {}).get("perplexity", 0)
                        if ppl:
                            ppl_values.append(float(ppl))
                    except:
                        continue
            
            if ppl_values:
                total = len(ppl_values)
                avg_ppl = sum(ppl_values) / total
                print(f"统计样本数: {total}")
                print(f"平均PPL: {avg_ppl:.2f}")
                print(f"最小PPL: {min(ppl_values):.2f}")
                print(f"最大PPL: {max(ppl_values):.2f}")
        
    finally:
        # 清理临时配置
        if temp_yaml_path.exists():
            temp_yaml_path.unlink()


# ==================== 统计输出 ====================

def print_ppl_stats(ppl_values, total, output_file):
    """打印PPL统计信息"""
    avg_ppl = sum(ppl_values) / len(ppl_values)
    min_ppl = min(ppl_values)
    max_ppl = max(ppl_values)
    
    sorted_ppl = sorted(ppl_values)
    mid = len(sorted_ppl) // 2
    median_ppl = sorted_ppl[mid] if len(sorted_ppl) % 2 == 1 else (sorted_ppl[mid-1] + sorted_ppl[mid]) / 2
    
    print(f"\n✅ PPL计算完成!")
    print(f"总文本数: {total}")
    print(f"平均PPL: {avg_ppl:.2f}")
    print(f"最小PPL: {min_ppl:.2f}")
    print(f"最大PPL: {max_ppl:.2f}")
    print(f"中位数PPL: {median_ppl:.2f}")
    print(f"输出文件: {output_file}")


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(
        description="计算文本的PPL（困惑度）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 (方式1 - HuggingFace模型):
  %(prog)s input.jsonl -o output.jsonl
  %(prog)s input.jsonl -t text -m gpt2 -o output.jsonl

示例 (方式2 - data-juicer):
  %(prog)s input.jsonl -o output.jsonl --method dj
  %(prog)s input.jsonl -o output.jsonl --method dj --lang zh

支持的语言代码: en, zh, fr, de, es, ru, ja, ar 等
        """
    )
    
    parser.add_argument("input", help="输入JSONL文件路径")
    parser.add_argument("-o", "--output", default="output_ppl.jsonl", help="输出JSONL文件路径")
    parser.add_argument("-t", "--field", default="text", help="文本字段名 (默认: text)")
    
    # 方式选择
    parser.add_argument("-m", "--method", choices=["hf", "dj"], default="hf",
                    help="计算方式: hf=HuggingFace模型, dj=data-juicer (默认: hf)")
    
    # HuggingFace参数
    parser.add_argument("--model", default="gpt2", help="HuggingFace模型名称 (默认: gpt2)")
    
    # data-juicer参数
    parser.add_argument("--lang", default="en", help="data-juicer语言代码 (默认: en)")
    parser.add_argument("--min-ppl", type=float, default=0, help="最小PPL阈值 (默认: 0)")
    parser.add_argument("--max-ppl", type=float, default=1500, help="最大PPL阈值 (默认: 1500)")
    
    args = parser.parse_args()
    
    if args.method == "hf":
        # 方式1: 使用HuggingFace模型
        model, tokenizer, device = load_hf_model(args.model)
        process_with_hf_model(
            model=model,
            tokenizer=tokenizer,
            input_path=args.input,
            text_field=args.field,
            output_path=args.output,
            device=device
        )
    else:
        # 方式2: 使用data-juicer
        process_with_data_juicer(
            input_path=args.input,
            text_field=args.field,
            output_path=args.output,
            lang=args.lang,
            min_ppl=args.min_ppl,
            max_ppl=args.max_ppl,
            export_stats=True
        )


if __name__ == "__main__":
    main()