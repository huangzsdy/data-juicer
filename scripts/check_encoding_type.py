import chardet
import argparse
import os


def detect_encoding(file_path):
    """
    检测文件的编码格式

    参数:
        file_path: 文件路径

    返回:
        检测到的编码格式字符串
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return f"错误: 文件 '{file_path}' 不存在"

        # 检查文件是否可读
        if not os.access(file_path, os.R_OK):
            return f"错误: 文件 '{file_path}' 不可读"

        # 以二进制模式读取文件内容
        with open(file_path, 'rb') as file:
            # 读取文件内容，可以限制读取大小以提高性能
            # 对于大文件，读取一部分通常就足够检测编码
            raw_data = file.read(100000)  # 读取最多100KB

            # 如果文件非常小，读取全部内容
            if len(raw_data) < 100:
                file.seek(0)
                raw_data = file.read()

        # 使用chardet检测编码
        result = chardet.detect(raw_data)

        # 返回检测结果
        encoding = result['encoding']
        confidence = result['confidence']

        return f"检测结果:\n  文件: {file_path}\n  编码: {encoding}\n  置信度: {confidence:.2%}"

    except Exception as e:
        return f"检测过程中发生错误: {str(e)}"


def main():
    """
    主函数，处理命令行参数并执行编码检测
    """
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='检测文件的编码格式')
    parser.add_argument('file', help='要检测编码的文件路径')

    # 解析命令行参数
    args = parser.parse_args()

    # 检测文件编码
    result = detect_encoding(args.file)

    # 输出结果
    print(result)


if __name__ == "__main__":
    main()