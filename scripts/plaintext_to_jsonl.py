import os
import json
import argparse


def convert_txt_to_jsonl(input_folder, output_file):
    """
    将文件夹中所有txt文件的每一行转换为JSONL格式

    Args:
        input_folder: 包含txt文件的文件夹路径
        output_file: 输出的jsonl文件路径
    """
    # 获取文件夹中所有txt文件
    txt_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]

    if not txt_files:
        print(f"警告: 在文件夹 {input_folder} 中未找到txt文件")
        return

    print(f"找到 {len(txt_files)} 个txt文件:")

    # 打开输出文件
    with open(output_file, 'w', encoding='utf-8') as out_f:
        total_lines = 0

        # 遍历每个txt文件
        for txt_file in txt_files:
            file_path = os.path.join(input_folder, txt_file)

            try:
                with open(file_path, 'r', encoding='utf-8') as in_f:
                    for line_num, line in enumerate(in_f, 1):
                        # 去除行尾换行符
                        line = line.rstrip('\n')

                        # 创建JSON对象
                        json_obj = {"text": line}

                        # 写入JSONL文件
                        json_line = json.dumps(json_obj, ensure_ascii=False)
                        out_f.write(json_line + '\n')

                        total_lines += 1

            except Exception as e:
                print(f"处理文件 {txt_file} 时出错: {e}")

    print(f"\n转换完成!")
    print(f"总计: {total_lines} 行")
    print(f"输出文件: {output_file}")


def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='将txt文件转换为JSONL格式')
    parser.add_argument('input_folder', help='包含txt文件的文件夹路径')
    parser.add_argument('output_file', nargs='?', default='output.jsonl',
                        help='输出JSONL文件路径 (默认: output.jsonl)')

    # 解析命令行参数
    args = parser.parse_args()

    # 检查输入文件夹是否存在
    if not os.path.isdir(args.input_folder):
        print(f"错误: 文件夹 '{args.input_folder}' 不存在")
        return

    # 执行转换
    convert_txt_to_jsonl(args.input_folder, args.output_file)


if __name__ == "__main__":
    main()