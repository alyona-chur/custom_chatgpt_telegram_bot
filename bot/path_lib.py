from pathlib import Path


def get_absolute_path(relative_path, root_dir):
    parts = relative_path.split('/')
    res_path = Path(*parts)
    if root_dir is not None:
        res_path = Path(root_dir) / res_path
    return res_path
