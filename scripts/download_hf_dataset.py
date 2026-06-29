import os
import argparse
import sys
from datasets import load_dataset, IterableDataset
from huggingface_hub import whoami
import json


# ======================
# Hugging Face 镜像与认证支持
# ======================
def setup_hf_env(use_mirror: bool = False, token: str = None):
    """
    设置 HF 镜像和认证
    """
    # 1. 设置镜像
    if use_mirror:
        mirror_url = "https://hf-mirror.com"
        os.environ["HF_ENDPOINT"] = mirror_url
        print(f"🌐 已启用 Hugging Face 镜像: {mirror_url}")
    else:
        os.environ.pop("HF_ENDPOINT", None)

    # 2. 处理 Token
    if token:
        # 优先使用传入的 token
        try:
            whoami(token=token)
            print("✅ 使用提供的 Hugging Face Token 认证成功")
        except Exception as e:
            print(f"❌ Token 无效或无法连接: {e}", file=sys.stderr)
            sys.exit(1)
        return token
    else:
        return None


def download_and_save_dataset(
        dataset_name: str,
        subset: str = None,
        split: str = "train",
        save_dir: str = "./data",
        use_mirror: bool = False,
        hf_token: str = None
):
    token = setup_hf_env(use_mirror=use_mirror, token=hf_token)

    os.makedirs(save_dir, exist_ok=True)

    print(f"\n📥 正在加载数据集: '{dataset_name}'")
    load_kwargs = {
        "path": dataset_name,
        "split": split,
        "streaming": True,
        "token": token
    }
    if subset:
        print(f"   子集 (config): {subset}")
        load_kwargs["name"] = subset

    try:
        dataset = load_dataset(**load_kwargs)
    except Exception as e:
        print(f"❌ 加载数据集失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 生成安全文件名
    safe_name = dataset_name.replace("/", "__")
    subset_str = f"_{subset}" if subset else ""
    filename = f"{safe_name}{subset_str}_{split}.jsonl"
    filepath = os.path.join(save_dir, filename)

    count = 0
    with open(filepath, "w", encoding="utf-8") as f_out:
        for item in dataset:
            f_out.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
            count += 1
            if count % 10000 == 0:
                print(f"  已保存 {count} 条", end="\r")

    print(f"\n💾 已保存至: {os.path.abspath(filepath)}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="从 Hugging Face 下载数据集（支持镜像加速 + Token 认证）"
    )
    parser.add_argument("--dataset", type=str, required=True, help="Hugging Face 数据集名称")
    parser.add_argument("--subset", type=str, default=None, help="子集名称（config），如 'mn'")
    parser.add_argument("--split", type=str, default="train", help="数据分割，默认 'train'")
    parser.add_argument("--save_dir", type=str, default="./data", help="保存目录")
    parser.add_argument("--use_mirror", action="store_true", help="启用 HF 镜像（推荐国内用户）")
    parser.add_argument("--token", type=str, default=None, help="Hugging Face Token（用于私有/受限数据集）")

    args = parser.parse_args()

    # 安全提示：避免在日志中泄露 token
    if args.token:
        masked_token = args.token[:4] + "..." + args.token[-4:] if len(args.token) > 8 else "..."
        print(f"🔑 使用 Token: {masked_token}")

    download_and_save_dataset(
        dataset_name=args.dataset,
        subset=args.subset,
        split=args.split,
        save_dir=args.save_dir,
        use_mirror=args.use_mirror,
        hf_token=args.token
    )