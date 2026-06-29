import json
import re
import sys
from pathlib import Path

# data-juicer 的 language_id_score_filter 只能辨认西里尔蒙古语，不能辨认传统蒙古语，因此单独写一个传统蒙古文筛选器

# 传统蒙古文 Unicode 范围
# 主区块: U+1800–U+18AF
# 补充区块: U+11660–U+1167F (Mongolian Supplement)
MONGOLIAN_PATTERN = re.compile(r'[\u1800-\u18AF\U00011660-\U0001167F]')

def mongolian_ratio(text):
    """计算文本中传统蒙古文字符的比例"""
    if not text:
        return 0.0
    total = len(text)
    mongolian_count = len(MONGOLIAN_PATTERN.findall(text))
    return mongolian_count / total

def main(input_path, field_name, output_path, threshold):
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"❌ 错误：输入文件 '{input_file}' 不存在。", file=sys.stderr)
        sys.exit(1)

    try:
        threshold = float(threshold)
        if not (0.0 <= threshold <= 1.0):
            raise ValueError
    except ValueError:
        print("❌ 错误：阈值必须是 0.0 到 1.0 之间的数字（如 0.7）", file=sys.stderr)
        sys.exit(1)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    kept = 0

    with open(input_file, 'r', encoding='utf-8') as fin, \
         open(output_file, 'w', encoding='utf-8') as fout:

        for line_num, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"⚠️ 警告：第 {line_num} 行不是有效 JSON，跳过。", file=sys.stderr)
                continue

            text = data.get(field_name, "")
            if not isinstance(text, str):
                continue

            total += 1

            ratio = mongolian_ratio(text)
            if ratio >= threshold:
                fout.write(line + '\n')
                kept += 1

            if total % 10000 == 0:
                print(f"已处理 {total} 行，已保留 {kept} 行...")

    print(f"\n✅ 完成！")
    print(f"阈值: ≥ {threshold:.2%} 传统蒙古文字符")
    print(f"总有效行数: {total}")
    print(f"匹配并保留的行数: {kept}")
    print(f"输出文件: {output_file}")

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("用法: python filter_mongolian_traditional.py <input.jsonl> <field_name> <output.jsonl> <threshold>")
        print("说明: threshold 是 0.0～1.0 之间的小数，表示蒙古文字符占比阈值")
        print("示例: python filter_mongolian_traditional.py data.jsonl text mongolian.jsonl 0.7")
        sys.exit(1)

    input_jsonl = sys.argv[1]
    field = sys.argv[2]
    output_jsonl = sys.argv[3]
    threshold = sys.argv[4]
    main(input_jsonl, field, output_jsonl, threshold)