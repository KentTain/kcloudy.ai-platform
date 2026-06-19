#!/usr/bin/env python3
"""
Alon 开发环境设置脚本
用于团队成员快速设置开发环境
"""

import subprocess
import sys
from pathlib import Path


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_command(cmd, description=""):
    """运行命令并处理错误"""
    if description:
        print(f"[INFO] {description}...")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f" 错误: {e}")
        if e.stderr:
            print(f"错误详情: {e.stderr}")
        return False, e.stderr


def check_requirements():
    """检查前置要求"""
    print(" 检查前置要求...")

    # 检查是否在项目根目录
    if not Path("pyproject.toml").exists():
        print(" 错误：请在项目根目录运行此脚本")
        return False

    # 检查是否在git仓库中
    if not Path(".git").exists():
        print(" 错误：当前目录不是git仓库")
        return False

    # 检查uv是否安装
    success, _ = run_command("uv --version")
    if not success:
        print(" 错误：uv 未安装")
        print("安装命令：")
        print("  macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh")
        print('  Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"')
        return False

    print(" 前置要求检查通过")
    return True


def install_workspace_dependencies():
    """安装 workspace 依赖"""
    print(" 安装 workspace 依赖...")

    success, _ = run_command("uv sync --inexact --group dev")
    if not success:
        print(" 根依赖安装失败")
        return False
    print("  ✓ 根项目依赖已安装")

    success, output = run_command("uv sync --inexact")
    if success:
        print("  ✓ Workspace 成员依赖已安装")
    else:
        print(f"  ⚠️  Workspace 依赖安装部分失败: {output[:200] if output else ''}")

    # 3. 安装 platform 的 dependency-groups
    platform_groups = [
        "standard",
        "database",
        "knowledge_base",
        "storage",
        "tool",
        "plugin",
        "discovery",
        "graphrag",
    ]

    print("  正在安装 platform dependency-groups...")
    groups_str = " ".join(f"--group {g}" for g in platform_groups)
    cmd = f"uv sync --inexact --package alon-platform {groups_str}"
    success, output = run_command(cmd)
    if success:
        print("    ✓ 所有 dependency-groups 已安装")
    else:
        for group in platform_groups:
            cmd = f"uv sync --inexact --package alon-platform --group {group}"
            success, output = run_command(cmd)
            if success:
                print(f"    ✓ [{group}] 已安装")
            else:
                output_lower = (output or "").lower()
                if (
                    "error" in output_lower
                    or "not found" in output_lower
                    or "no dependency group" in output_lower
                ):
                    print(f"    ⚠️  [{group}] 未配置")
                else:
                    print(f"    ✗ [{group}] 安装失败: {(output or '')[:100]}")

    print("  依赖安装完成")
    return True


def discover_apps_packages():
    """扫描 apps 目录下的子模块"""
    apps_dir = Path("apps")
    if not apps_dir.exists():
        return []

    packages = []
    for app_dir in apps_dir.iterdir():
        if app_dir.is_dir() and (app_dir / "pyproject.toml").exists():
            packages.append(app_dir.name)
    return sorted(packages)


def install_apps_dependencies():
    """安装 apps 子模块依赖"""
    print(" 安装 apps 子模块依赖...")

    apps_packages = discover_apps_packages()
    if not apps_packages:
        print("  ⚠️  未发现 apps 子模块")
        return True

    for app_name in apps_packages:
        cmd = f"uv sync --inexact --package {app_name}"
        success, output = run_command(cmd, f"安装 {app_name}")
        if success:
            print(f"  ✓ [{app_name}] 依赖已安装")
        else:
            output_lower = (output or "").lower()
            if (
                "error" in output_lower
                or "not found" in output_lower
                or "no such package" in output_lower
            ):
                print(f"  ⚠️  [{app_name}] 未找到或未配置")
            else:
                print(f"  ✗ [{app_name}] 安装失败: {(output or '')[:100]}")

    print("  apps 子模块依赖安装完成")
    return True


def install_frontend_dependencies():
    """安装前端依赖（需要 Node >= 22.16.0 和 pnpm）"""
    print(" 检查前端环境...")

    # 检查 node 版本
    success, output = run_command("node --version")
    if not success:
        print("  ⚠️  Node.js 未安装，跳过前端依赖安装")
        return True

    node_version = output.strip().lstrip("v")
    try:
        major, minor, patch = (int(x) for x in node_version.split(".")[:3])
        if (major, minor, patch) < (22, 16, 0):
            print(
                f"  ⚠️  Node.js 版本过低（当前 {node_version}，需要 >= 22.16.0），跳过前端依赖安装"
            )
            return True
    except (ValueError, IndexError):
        print(f"  ⚠️  无法解析 Node.js 版本（{node_version}），跳过前端依赖安装")
        return True

    # 检查 pnpm
    success, output = run_command("pnpm --version")
    if not success:
        print("  ⚠️  pnpm 未安装，跳过前端依赖安装")
        print("  安装命令：npm install -g pnpm")
        return True

    success, _ = run_command("pnpm install", "安装前端依赖")
    if success:
        print("  ✓ 前端依赖已安装")
    else:
        print("  ✗ 前端依赖安装失败")

    return True


def install_pre_commit_hooks():
    """安装pre-commit hooks"""
    print(" 设置 pre-commit hooks...")

    # 安装pre-commit hook
    success, _ = run_command("uv run pre-commit install")
    if not success:
        print(" pre-commit hook 安装失败")
        return False

    # 安装commit-msg hook
    success, _ = run_command("uv run pre-commit install --hook-type commit-msg")
    if not success:
        print(" commit-msg hook 安装失败")
        return False

    print(" pre-commit hooks 安装成功")
    return True


def verify_setup():
    """验证设置"""
    print(" 验证 pre-commit 配置...")

    success, _ = run_command("uv run pre-commit run --all-files")
    if success:
        print(" pre-commit 配置验证成功")
    else:
        print(" pre-commit 检查发现问题，已自动修复")
        print("请检查修改的文件，如有需要请重新提交")

    return True


def main():
    """主函数"""
    print(" 设置 Alon 开发环境...")
    print()

    # 检查前置要求
    if not check_requirements():
        sys.exit(1)

    print()

    # 安装依赖
    if not install_workspace_dependencies():
        sys.exit(1)

    print()

    # 安装 apps 子模块依赖
    if not install_apps_dependencies():
        sys.exit(1)

    print()

    # 安装前端依赖
    install_frontend_dependencies()

    print()

    # 安装pre-commit hooks
    if not install_pre_commit_hooks():
        sys.exit(1)

    print()

    # 验证设置
    verify_setup()

    print()
    print(" 开发环境设置完成！")
    print()
    print(" 常用命令：")
    print("  uv run --package alon-platform alon --help      # 查看平台命令")
    print("  uv run --package alon-platform runserver        # 启动开发服务器")
    print("  uv run --package alon-platform runtask          # 启动任务调度器")
    print("  uv run pre-commit run --all-files               # 手动运行代码检查")
    print("  uv run format-code                              # 格式化代码")
    print("  uv run check-dev                                # 检查开发环境")
    print()
    print(" 提示：现在每次 git commit 都会自动运行代码检查和格式化")


if __name__ == "__main__":
    main()
