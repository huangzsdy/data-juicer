#!/usr/bin/env python3
"""
文件编码转换脚本
将非UTF-8编码的文件转换为UTF-8编码
"""

import chardet
import argparse
import os
import sys
from pathlib import Path


def detect_file_encoding(file_path, sample_size=100000):
    """
    检测文件的编码格式

    参数:
        file_path: 文件路径
        sample_size: 采样大小（字节数）

    返回:
        (encoding, confidence): 编码格式和置信度
    """
    try:
        with open(file_path, 'rb') as file:
            # 读取文件内容进行编码检测
            raw_data = file.read(sample_size)

        # 使用chardet检测编码
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']

        # 如果置信度太低或者编码为None，尝试读取更多数据
        if confidence < 0.5 or encoding is None:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']

        return encoding, confidence
    except Exception as e:
        raise RuntimeError(f"检测文件编码失败: {str(e)}")


def convert_to_utf8(input_file, output_file=None, backup=True, verbose=True):
    """
    将文件转换为UTF-8编码

    参数:
        input_file: 输入文件路径
        output_file: 输出文件路径（默认与输入文件相同）
        backup: 是否创建备份文件
        verbose: 是否显示详细信息

    返回:
        成功返回True，失败返回False
    """
    try:
        # 获取绝对路径
        input_path = Path(input_file).resolve()

        # 检查输入文件是否存在
        if not input_path.exists():
            print(f"错误: 输入文件 '{input_file}' 不存在")
            return False

        # 设置输出文件路径
        if output_file is None:
            output_path = input_path
        else:
            output_path = Path(output_file).resolve()

        # 检测文件编码
        if verbose:
            print(f"正在检测文件编码: {input_path}")

        detected_encoding, confidence = detect_file_encoding(input_path)

        if detected_encoding is None:
            print(f"错误: 无法检测文件编码")
            return False

        if verbose:
            print(f"检测到编码: {detected_encoding} (置信度: {confidence:.2%})")

        # 如果已经是UTF-8编码，无需转换
        if detected_encoding.lower() in ['utf-8', 'utf_8', 'utf8']:
            print(f"文件已经是UTF-8编码，无需转换")
            return True

        # 如果置信度太低，提示用户
        if confidence < 0.6:
            print(f"警告: 编码检测置信度较低 ({confidence:.2%})，转换可能不准确")
            if verbose:
                response = input("是否继续? (y/n): ")
                if response.lower() != 'y':
                    print("转换已取消")
                    return False

        # 创建备份文件（如果需要）
        backup_path = None
        if backup and output_path == input_path:
            backup_path = input_path.with_suffix(input_path.suffix + '.bak')
            try:
                import shutil
                shutil.copy2(input_path, backup_path)
                if verbose:
                    print(f"已创建备份文件: {backup_path}")
            except Exception as e:
                print(f"警告: 无法创建备份文件: {str(e)}")

        # 读取源文件内容
        if verbose:
            print(f"正在读取文件: {input_path}")

        try:
            # 使用检测到的编码读取文件
            with open(input_path, 'r', encoding=detected_encoding, errors='replace') as f:
                content = f.read()
        except (UnicodeDecodeError, LookupError) as e:
            # 如果检测到的编码无法解码，尝试常见编码
            if verbose:
                print(f"使用检测到的编码 '{detected_encoding}' 解码失败: {str(e)}")
                print("正在尝试其他常见编码...")

            common_encodings = ['gb2312', 'gbk', 'gb18030', 'big5', 'shift_jis',
                                'euc-jp', 'iso-8859-1', 'windows-1252', 'latin-1']

            for encoding in common_encodings:
                try:
                    with open(input_path, 'r', encoding=encoding, errors='strict') as f:
                        content = f.read()
                    detected_encoding = encoding
                    if verbose:
                        print(f"成功使用编码 '{encoding}' 解码文件")
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                print(f"错误: 无法使用任何编码解码文件")
                return False

        # 写入UTF-8编码的文件
        if verbose:
            print(f"正在写入UTF-8文件: {output_path}")

        with open(output_path, 'w', encoding='utf-8', errors='strict') as f:
            f.write(content)

        if verbose:
            print(f"转换完成!")
            if backup_path and backup_path.exists():
                print(f"原始文件已备份到: {backup_path}")

        return True

    except Exception as e:
        print(f"转换过程中发生错误: {str(e)}")
        return False


def main():
    """
    主函数，处理命令行参数并执行转换
    """
    parser = argparse.ArgumentParser(
        description='将非UTF-8编码的文件转换为UTF-8编码',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.txt                # 将input.txt转换为UTF-8，创建备份文件
  %(prog)s input.txt -o output.txt  # 转换并保存为output.txt
  %(prog)s input.txt -n             # 不创建备份文件
  %(prog)s *.txt                    # 批量转换所有txt文件
        """
    )

    parser.add_argument('input_files', nargs='+',
                        help='要转换的文件（支持通配符）')
    parser.add_argument('-o', '--output', metavar='FILE',
                        help='输出文件路径（单个文件转换时使用）')
    parser.add_argument('-n', '--no-backup', action='store_true',
                        help='不创建备份文件')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='安静模式，不显示详细信息')
    parser.add_argument('-f', '--force', action='store_true',
                        help='强制转换，即使已经是UTF-8编码')

    args = parser.parse_args()

    # 扩展通配符（Windows可能需要额外处理）
    import glob
    expanded_files = []
    for pattern in args.input_files:
        matched_files = glob.glob(pattern)
        if matched_files:
            expanded_files.extend(matched_files)
        else:
            # 如果没有匹配到文件，直接使用原参数（可能是未匹配到的单个文件）
            expanded_files.append(pattern)

    # 去除重复的文件
    input_files = list(set(expanded_files))

    if not input_files:
        print("错误: 未找到指定的文件")
        sys.exit(1)

    # 批量处理文件
    successful = 0
    failed = 0

    for i, input_file in enumerate(input_files):
        if len(input_files) > 1:
            print(f"\n处理文件 {i + 1}/{len(input_files)}: {input_file}")

        # 设置输出文件路径
        output_file = args.output if (args.output and len(input_files) == 1) else None

        # 执行转换
        if convert_to_utf8(
                input_file=input_file,
                output_file=output_file,
                backup=not args.no_backup,
                verbose=not args.quiet
        ):
            successful += 1
        else:
            failed += 1

    # 输出统计信息
    if len(input_files) > 1:
        print(f"\n转换完成: {successful} 个成功, {failed} 个失败")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()