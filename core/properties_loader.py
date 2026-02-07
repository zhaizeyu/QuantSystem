"""
从 config/config.properties 加载配置，供 core.config 与 backtest_config 使用。
"""
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "config.properties"

_props: Optional[dict] = None


def _parse_properties(path: Path) -> dict:
    out = {}
    if not path.exists():
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            idx = line.find("=")
            if idx < 0:
                continue
            key = line[:idx].strip().lower()
            value = line[idx + 1 :].strip()
            out[key] = value
    return out


def get_properties() -> dict:
    """获取全部 key=value，键为小写。"""
    global _props
    if _props is None:
        _props = _parse_properties(CONFIG_FILE)
    return _props


def get(key: str, default: Optional[str] = None) -> Optional[str]:
    """获取单个键，键名小写。空字符串视为未设置，返回 default。"""
    p = get_properties()
    v = p.get(key.lower())
    if v is None or v == "":
        return default
    return v


def get_int(key: str, default: Optional[int] = None) -> Optional[int]:
    v = get(key)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def get_float(key: str, default: Optional[float] = None) -> Optional[float]:
    v = get(key)
    if v is None:
        return default
    try:
        return float(v)
    except ValueError:
        return default
