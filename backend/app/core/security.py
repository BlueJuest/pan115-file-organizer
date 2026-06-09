ILLEGAL_PATH_CHARS = '<>:"/\\|?*'


def mask_secret(value: str | None, visible: int = 4) -> str:
    if not value:
        return ""

    keep = max(visible, 0)
    if keep == 0:
        return "*" * len(value)
    if len(value) <= keep:
        return "*" * len(value)

    return value[:keep] + "*" * max(len(value) - keep - 1, 0) + value[-keep:]


def clean_path_part(value: str) -> str:
    return "".join("_" if char in ILLEGAL_PATH_CHARS else char for char in value)
