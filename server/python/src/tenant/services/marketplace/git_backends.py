"""Git 后端实现"""
from __future__ import annotations
from pathlib import Path
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import git as GitPythonRepo


class GitPythonBackend:
    """基于 GitPython 的 Git 后端实现"""

    def __init__(self, git_module):
        """
        初始化 GitPython 后端

        Args:
            git_module: GitPython 模块对象
        """
        self.git = git_module

    async def clone(self, repo_url: str, ref: str, target_path: Path, subdir: str | None) -> tuple[Path, str]:
        """
        克隆仓库

        Args:
            repo_url: 仓库 URL
            ref: Git 引用
            target_path: 目标路径
            subdir: 子目录路径（用于稀疏检出）

        Returns:
            元组 (仓库路径, 提交 SHA)
        """
        # GitPython 克隆
        repo = self.git.Repo.clone_from(repo_url, target_path, branch=ref)

        # 如果指定了子目录，配置稀疏检出
        if subdir:
            await self._setup_sparse_checkout(repo, subdir)

        # 获取当前提交 SHA
        commit_sha = repo.head.commit.hexsha
        return target_path, commit_sha

    async def fetch_and_checkout(self, repo_path: Path, ref: str, subdir: str | None) -> str:
        """
        拉取更新并切换引用

        Args:
            repo_path: 仓库路径
            ref: Git 引用
            subdir: 子目录路径（用于稀疏检出）

        Returns:
            提交 SHA
        """
        repo = self.git.Repo(repo_path)

        # 拉取最新代码
        origin = repo.remotes.origin
        origin.fetch()

        # 切换到指定引用
        repo.git.checkout(ref)

        # 拉取更新
        repo.git.pull("origin", ref)

        # 如果指定了子目录，更新稀疏检出
        if subdir:
            await self._setup_sparse_checkout(repo, subdir)

        # 返回当前提交 SHA
        return repo.head.commit.hexsha

    async def _setup_sparse_checkout(self, repo: "GitPythonRepo.Repo", subdir: str) -> None:
        """
        配置稀疏检出

        Args:
            repo: GitPython 仓库对象
            subdir: 子目录路径
        """
        # 启用稀疏检出
        repo.git.config("core.sparseCheckout", "true")

        # 写入稀疏检出配置
        sparse_checkout_file = repo.git_dir / "info" / "sparse-checkout"
        sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
        sparse_checkout_file.write_text(f"{subdir}\n", encoding="utf-8")

        # 重新应用稀疏检出
        repo.git.read_tree("-mu", "HEAD")


class SubprocessGitBackend:
    """基于子进程调用 git 命令的后端实现"""

    async def clone(self, repo_url: str, ref: str, target_path: Path, subdir: str | None) -> tuple[Path, str]:
        """
        克隆仓库

        Args:
            repo_url: 仓库 URL
            ref: Git 引用
            target_path: 目标路径
            subdir: 子目录路径（用于稀疏检出）

        Returns:
            元组 (仓库路径, 提交 SHA)
        """
        # 如果指定了子目录，使用稀疏克隆
        if subdir:
            await self._sparse_clone(repo_url, ref, target_path, subdir)
        else:
            # 普通克隆
            cmd = ["git", "clone", "--branch", ref, repo_url, str(target_path)]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise RuntimeError(f"Git clone failed: {stderr.decode()}")

        # 获取当前提交 SHA
        commit_sha = await self._get_commit_sha(target_path)
        return target_path, commit_sha

    async def fetch_and_checkout(self, repo_path: Path, ref: str, subdir: str | None) -> str:
        """
        拉取更新并切换引用

        Args:
            repo_path: 仓库路径
            ref: Git 引用
            subdir: 子目录路径（用于稀疏检出）

        Returns:
            提交 SHA
        """
        # 拉取最新代码
        fetch_cmd = ["git", "fetch", "origin"]
        process = await asyncio.create_subprocess_exec(
            *fetch_cmd,
            cwd=str(repo_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Git fetch failed: {stderr.decode()}")

        # 切换到指定引用
        checkout_cmd = ["git", "checkout", ref]
        process = await asyncio.create_subprocess_exec(
            *checkout_cmd,
            cwd=str(repo_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Git checkout failed: {stderr.decode()}")

        # 拉取更新
        pull_cmd = ["git", "pull", "origin", ref]
        process = await asyncio.create_subprocess_exec(
            *pull_cmd,
            cwd=str(repo_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Git pull failed: {stderr.decode()}")

        # 如果指定了子目录，更新稀疏检出
        if subdir:
            await self._update_sparse_checkout(repo_path, subdir)

        # 返回当前提交 SHA
        return await self._get_commit_sha(repo_path)

    async def _sparse_clone(self, repo_url: str, ref: str, target_path: Path, subdir: str) -> None:
        """
        稀疏克隆仓库

        Args:
            repo_url: 仓库 URL
            ref: Git 引用
            target_path: 目标路径
            subdir: 子目录路径
        """
        # 初始化仓库
        await self._run_git_command(["git", "init"], target_path.parent)
        await self._run_git_command(["git", "remote", "add", "origin", repo_url], target_path)

        # 启用稀疏检出
        await self._run_git_command(["git", "config", "core.sparseCheckout", "true"], target_path)

        # 写入稀疏检出配置
        sparse_checkout_file = target_path / ".git" / "info" / "sparse-checkout"
        sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
        sparse_checkout_file.write_text(f"{subdir}\n", encoding="utf-8")

        # 拉取指定引用
        await self._run_git_command(["git", "pull", "origin", ref], target_path)

    async def _update_sparse_checkout(self, repo_path: Path, subdir: str) -> None:
        """
        更新稀疏检出配置

        Args:
            repo_path: 仓库路径
            subdir: 子目录路径
        """
        # 写入稀疏检出配置
        sparse_checkout_file = repo_path / ".git" / "info" / "sparse-checkout"
        sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
        sparse_checkout_file.write_text(f"{subdir}\n", encoding="utf-8")

        # 重新应用稀疏检出
        await self._run_git_command(["git", "read-tree", "-mu", "HEAD"], repo_path)

    async def _get_commit_sha(self, repo_path: Path) -> str:
        """
        获取当前提交 SHA

        Args:
            repo_path: 仓库路径

        Returns:
            提交 SHA
        """
        process = await asyncio.create_subprocess_exec(
            "git", "rev-parse", "HEAD",
            cwd=str(repo_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Failed to get commit SHA: {stderr.decode()}")
        return stdout.decode().strip()

    async def _run_git_command(self, cmd: list[str], cwd: Path) -> None:
        """
        执行 Git 命令

        Args:
            cmd: 命令和参数列表
            cwd: 工作目录
        """
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{stderr.decode()}")
