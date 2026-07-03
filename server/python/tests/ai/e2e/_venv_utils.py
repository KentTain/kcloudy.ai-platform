"""跨平台 venv 路径工具

复用生产代码 local_runtime.py:816-820 的跨平台逻辑，
集中管理测试中的 venv 路径处理。
"""
from pathlib import Path


def get_venv_python(venv_path: Path) -> Path:
    """获取虚拟环境的 Python 可执行文件路径（跨平台）。

    按顺序检查 Linux/macOS 和 Windows 的候选路径，
    返回第一个存在的路径。

    Args:
        venv_path: 虚拟环境根目录（如 .venv 目录）

    Returns:
        Python 可执行文件路径

    Raises:
        RuntimeError: 如果找不到任何 Python 解释器

    Example:
        >>> venv_path = Path(".venv")
        >>> python_path = get_venv_python(venv_path)
        >>> print(python_path)
        .venv/bin/python  # Linux/macOS
        .venv/Scripts/python.exe  # Windows
    """
    candidates = [
        venv_path / "bin" / "python",  # Linux/macOS
        venv_path / "bin" / "python3",  # Linux/macOS 备选
        venv_path / "Scripts" / "python.exe",  # Windows
    ]

    for path in candidates:
        if path.exists():
            return path

    raise RuntimeError(
        f"虚拟环境中未找到 Python 解释器: {[str(p) for p in candidates]}"
    )
