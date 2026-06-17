"""配置读取器实用工具类."""

from collections.abc import Callable
from contextlib import contextmanager
from enum import Enum
from typing import Any, TypeVar

from environs import Env

T = TypeVar("T")

KeyValue = str | Enum
EnvKeySet = str | list[str]


def read_key(value: KeyValue) -> str:
    """读取键值."""
    if not isinstance(value, str):
        return value.value.lower()
    return value.lower()


class EnvironmentReader:
    """配置读取器实用工具类."""

    _env: Env
    _config_stack: list[dict]

    def __init__(self, env: Env):
        """
        初始化实例。

        Args:
            env (Env): env 参数。
        """
        self._env = env
        self._config_stack = []

    @property
    def env(self):
        """获取环境对象."""
        return self._env

    def _read_env(
        self, env_key: str | list[str], default_value: T, read: Callable[[str, T], T]
    ) -> T | None:
        """
        读取read_env。

        Args:
            env_key (str | list[str]): env_key 参数。
            default_value (T): default_value 参数。
            read (Callable[[str, T], T]): read 参数。

        Returns:
            处理结果。
        """
        if isinstance(env_key, str):
            env_key = [env_key]

        for k in env_key:
            result = read(k.upper(), default_value)
            if result is not default_value:
                return result

        return default_value

    def envvar_prefix(self, prefix: KeyValue):
        """设置环境变量前缀."""
        prefix = read_key(prefix)
        prefix = f"{prefix}_".upper()
        return self._env.prefixed(prefix)

    def use(self, value: Any | None):
        """创建上下文管理器,将值推入配置栈."""

        @contextmanager
        def config_context():
            """
            处理config_context。

            Yields:
                迭代产生的结果。
            """
            self._config_stack.append(value or {})
            try:
                yield
            finally:
                self._config_stack.pop()

        return config_context()

    @property
    def section(self) -> dict:
        """获取当前节."""
        return self._config_stack[-1] if self._config_stack else {}

    def str(
        self,
        key: KeyValue,
        env_key: EnvKeySet | None = None,
        default_value: str | None = None,
    ) -> str | None:
        """读取配置值."""
        key = read_key(key)
        if self.section and key in self.section:
            return self.section[key]

        return self._read_env(
            env_key or key, default_value, (lambda k, dv: self._env(k, dv))
        )

    def int(
        self,
        key: KeyValue,
        env_key: EnvKeySet | None = None,
        default_value: int | None = None,
    ) -> int | None:
        """读取整数配置值."""
        key = read_key(key)
        if self.section and key in self.section:
            return int(self.section[key])
        return self._read_env(
            env_key or key, default_value, lambda k, dv: self._env.int(k, dv)
        )

    def bool(
        self,
        key: KeyValue,
        env_key: EnvKeySet | None = None,
        default_value: bool | None = None,
    ) -> bool | None:
        """读取布尔配置值."""
        key = read_key(key)
        if self.section and key in self.section:
            return bool(self.section[key])

        return self._read_env(
            env_key or key, default_value, lambda k, dv: self._env.bool(k, dv)
        )

    def float(
        self,
        key: KeyValue,
        env_key: EnvKeySet | None = None,
        default_value: float | None = None,
    ) -> float | None:
        """读取浮点数配置值."""
        key = read_key(key)
        if self.section and key in self.section:
            return float(self.section[key])
        return self._read_env(
            env_key or key, default_value, lambda k, dv: self._env.float(k, dv)
        )

    def list(
        self,
        key: KeyValue,
        env_key: EnvKeySet | None = None,
        default_value: list | None = None,
    ) -> list | None:
        """解析列表配置值."""
        key = read_key(key)
        result = None
        if self.section and key in self.section:
            result = self.section[key]
            if isinstance(result, list):
                return result

        if result is None:
            result = self.str(key, env_key)
        if result is not None:
            result = [s.strip() for s in result.split(",")]
            return [s for s in result if s]
        return default_value
