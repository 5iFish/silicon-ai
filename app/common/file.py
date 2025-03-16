import hashlib

def get_file_md5(file_path):
    """计算文件的md5值"""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()