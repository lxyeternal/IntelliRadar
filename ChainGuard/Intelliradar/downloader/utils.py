import os


def mkdir(*paths):
    """Create nested directory structure"""
    full_path = os.path.join(*paths)
    os.makedirs(full_path, exist_ok=True)
    return full_path

