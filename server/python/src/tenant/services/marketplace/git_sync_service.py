"""Git 仓库同步服务"""
from __future__ import annotations
from pathlib import Path
import re
import hashlib
import asyncio
import shutil
import subprocess
import time
from loguru import logger


class GitSyncService:
    """Git 仓库同步服务，负责克隆、更新和缓存 Git 仓库"""

    def __init__(self, cache_dir: Path | None = None):
        """
        初始化 GitSyncService

        Args:
            cache_dir: 缓存目录，默认为 ./cache/skills
        """
        self.cache_dir = cache_dir or Path("./cache/skills")

    def get_cache_path(self, repo_url: str, ref: str) -> Path:
        """
        根据仓库 URL 和引用获取缓存路径

        Args:
            repo_url: 仓库 URL
            ref: Git 引用（分支、标签或提交）

        Returns:
            缓存路径，格式为 {cache_dir}/{repo_name}/{ref}
        """
        # 解析 URL 提取主机名、所有者和仓库名
        match = re.search(r"https?://([^/]+)/([^/]+)/([^/]+?)(?:\.git)?$", repo_url)
        if match:
            host = match.group(1).replace(".", "_")
            owner = match.group(2)
            repo = match.group(3)
            repo_name = f"{host}_{owner}_{repo}"
        else:
            # 对于无法解析的 URL，使用 SHA256 哈希值作为仓库名
            repo_hash = hashlib.sha256(repo_url.encode()).hexdigest()[:12]
            repo_name = repo_hash

        return self.cache_dir / repo_name / ref

    def parse_source_url(self, source_url: str) -> tuple[str, str, str | None]:
        """
        解析源 URL，提取仓库 URL、引用和子目录

        Args:
            source_url: 源 URL，支持以下格式：
                - GitHub tree URL: https://github.com/{owner}/{repo}/tree/{ref}/{path}
                - GitHub blob URL: https://github.com/{owner}/{repo}/blob/{ref}/{path}
                - Git URL: https://github.com/{owner}/{repo}.git

        Returns:
            元组 (repo_url, ref, subdir)，其中 subdir 可能为 None
        """
        # 尝试匹配 GitHub tree/blob URL
        tree_match = re.search(
            r"https?://github\.com/([^/]+)/([^/]+)/(?:tree|blob)/([^/]+)/(.+)$",
            source_url
        )
        if tree_match:
            owner = tree_match.group(1)
            repo = tree_match.group(2)
            ref = tree_match.group(3)
            subdir = tree_match.group(4)
            repo_url = f"https://github.com/{owner}/{repo}.git"
            return repo_url, ref, subdir

        # 默认处理为普通 Git URL
        if source_url.endswith(".git"):
            return source_url, "main", None

        return source_url, "main", None

    async def sync_repo(self, repo_url: str, ref: str = "main", subdir: str | None = None) -> tuple[Path, str]:
        """
        同步 Git 仓库到本地缓存

        Args:
            repo_url: 仓库 URL
            ref: Git 引用（分支、标签或提交），默认为 main
            subdir: 子目录路径（用于稀疏检出），可选

        Returns:
            元组 (本地仓库路径, 提交 SHA)
        """
        cache_path = self.get_cache_path(repo_url, ref)
        cache_path.mkdir(parents=True, exist_ok=True)

        if (cache_path / ".git").exists():
            logger.info(f"Updating existing cache: {cache_path}")
            commit_sha = await self._fetch_and_checkout(cache_path, ref, subdir)
        else:
            logger.info(f"Cloning repository: {repo_url}")
            cache_path, commit_sha = await self._clone_repo(repo_url, ref, cache_path, subdir)

        return cache_path, commit_sha

    async def _clone_repo(self, repo_url: str, ref: str, target_path: Path, subdir: str | None) -> tuple[Path, str]:
        """
        克隆仓库到目标路径

        Args:
            repo_url: 仓库 URL
            ref: Git 引用
            target_path: 目标路径
            subdir: 子目录路径（用于稀疏检出）

        Returns:
            元组 (仓库路径, 提交 SHA)
        """
        backend = await self._get_git_backend()
        return await backend.clone(repo_url, ref, target_path, subdir)

    async def _fetch_and_checkout(self, repo_path: Path, ref: str, subdir: str | None) -> str:
        """
        拉取更新并切换到指定引用

        Args:
            repo_path: 仓库路径
            ref: Git 引用
            subdir: 子目录路径（用于稀疏检出）

        Returns:
            提交 SHA
        """
        backend = await self._get_git_backend()
        return await backend.fetch_and_checkout(repo_path, ref, subdir)

    async def check_repo_accessible(self, repo_url: str, ref: str) -> bool:
        """检查远程仓库和指定引用是否可访问

        同时检查分支（refs/heads/）和标签（refs/tags/）。

        Args:
            repo_url: 仓库 URL
            ref: Git 引用（分支名或标签名）

        Returns:
            True 如果仓库和引用可访问，否则 False
        """
        try:
            # 先检查分支
            cmd = ["git", "ls-remote", "--exit-code", repo_url, f"refs/heads/{ref}"]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            if proc.returncode == 0:
                return True

            # 再检查标签
            cmd = ["git", "ls-remote", "--exit-code", repo_url, f"refs/tags/{ref}"]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            return proc.returncode == 0
        except Exception:
            return False

    async def get_remote_commit_sha(self, repo_url: str, ref: str) -> str:
        """获取远程仓库指定引用的最新提交 SHA

        同时检查分支和标签。

        Args:
            repo_url: 仓库 URL
            ref: Git 引用（分支名或标签名）

        Returns:
            提交 SHA 字符串，获取失败返回空字符串
        """
        try:
            # 先查分支
            cmd = ["git", "ls-remote", repo_url, f"refs/heads/{ref}"]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            line = stdout.decode().strip()
            if line:
                return line.split("\t")[0]

            # 再查标签
            cmd = ["git", "ls-remote", repo_url, f"refs/tags/{ref}"]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            line = stdout.decode().strip()
            if line:
                # 标签可能是 annotated tag，返回 ^{} 行（指向的 commit）
                for l in line.split("\n"):
                    if l.endswith("^{}"):
                        return l.split("\t")[0]
                return line.split("\t")[0]

            return ""
        except Exception:
            return ""

    async def _get_git_backend(self):
        """
        获取 Git 后端实现

        优先使用 GitPython，如果不可用则回退到子进程方式

        Returns:
            Git 后端实例
        """
        try:
            import git
            from tenant.services.marketplace.git_backends import GitPythonBackend
            return GitPythonBackend(git)
        except ImportError:
            from tenant.services.marketplace.git_backends import SubprocessGitBackend
            return SubprocessGitBackend()

    def cleanup_expired(self, ttl_days: int = 30) -> int:
        """清理过期缓存目录

        Args:
            ttl_days: 缓存保留天数，超过此天数的缓存将被清理

        Returns:
            清理的目录数量
        """
        if not self.cache_dir.exists():
            return 0

        cutoff = time.time() - ttl_days * 86400
        removed = 0

        # 遍历 cache_dir 下的仓库目录（两层结构: repo_name/ref/）
        for repo_dir in self.cache_dir.iterdir():
            if not repo_dir.is_dir():
                continue
            for ref_dir in repo_dir.iterdir():
                if not ref_dir.is_dir():
                    continue
                # 使用目录修改时间判断过期
                try:
                    if ref_dir.stat().st_mtime < cutoff:
                        shutil.rmtree(ref_dir)
                        removed += 1
                        logger.info(f"清理过期缓存: {ref_dir}")
                except OSError as e:
                    logger.warning(f"清理缓存失败: {ref_dir}, 错误: {e}")

        return removed
