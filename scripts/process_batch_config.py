import yaml
import subprocess
import re
import os
import argparse

def update_yaml_file(yaml_file, file_number, total_file_number):
    """
    更新YAML文件中的文件名

    参数:
        yaml_file: YAML文件路径
        file_number: 当前文件编号
        total_file_number: 总文件编号

    返回:
        更新后的YAML内容
    """
    with open(yaml_file, 'r', encoding='utf-8') as f:
        yaml_content = f.read()

    # 格式化文件编号
    formatted_curr_number = f"{file_number:05d}"
    formatted_total_number = f"{total_file_number:05d}"

    # 构建新文件名
    new_filename = f"train-{formatted_curr_number}-of-{formatted_total_number}.jsonl"

    # 查找所有匹配的文件名
    matches = re.findall(r'train-\d{5}-of-\d{5}\.jsonl', yaml_content)

    # 对每个找到的文件名进行替换
    for old_filename in set(matches):
        yaml_content = yaml_content.replace(old_filename, new_filename)

    return yaml_content

def run_dj_process(yaml_content, yaml_file, file_number):
    """
    运行dj-process命令

    参数:
        yaml_content: YAML内容
        yaml_file: 临时YAML文件路径
    """
    # 将更新后的内容写入临时文件
    temp_yaml_file = f"temp_pipeline_config_{file_number:05d}.yaml"
    with open(temp_yaml_file, 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    try:
        # 运行dj-process命令
        cmd = ["dj-process", "--config", temp_yaml_file]
        print(f"运行命令: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        print("命令执行成功!")
        print("标准输出:", result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"命令执行失败，错误码: {e.returncode}")
        print("标准错误输出:", e.stderr)
        raise
    finally:
        # 清理临时文件
        if os.path.exists(temp_yaml_file):
            os.remove(temp_yaml_file)


def main():
    parser = argparse.ArgumentParser(description='批量处理JSONL文件')
    parser.add_argument('--start', type=int, default=0,
                        help='起始文件编号')
    parser.add_argument('--end', type=int, default=0,
                        help='结束文件编号')
    parser.add_argument('--total', type=int, default=0,
                        help='文件编号总数')
    parser.add_argument('--filepath', type=str,
                        default='config.yaml',
                        help='data-juicer config.yaml 配置文件路径（默认: config.yaml）')

    args = parser.parse_args()

    # 检查配置文件是否存在
    if not os.path.exists(args.filepath):
        print(f"错误: 配置文件 {args.filepath} 不存在")
        return

    print(f"开始批量处理文件 {args.start:05d} 到 {args.end:05d}")
    print(f"使用配置文件: {args.filepath}")

    for file_number in range(args.start, args.end + 1):
        print(f"\n{'=' * 60}")
        print(f"处理文件: train-{file_number:05d}-of-{args.total:05d}.jsonl")
        print(f"{'=' * 60}")

        try:
            # 更新YAML文件内容
            updated_yaml = update_yaml_file(args.filepath, file_number, args.total)
            run_dj_process(updated_yaml, args.filepath, file_number)

        except Exception as e:
            print(f"处理文件 train-{file_number:05d}-of-{args.total:05d}.jsonl 时出错: {e}")
            print("是否继续处理下一个文件？(y/n)")
            choice = input().strip().lower()
            if choice != 'y':
                print("终止处理")
                break

    print("\n处理完成!")


if __name__ == "__main__":
    main()