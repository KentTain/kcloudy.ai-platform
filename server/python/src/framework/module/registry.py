"""
模块注册中心

管理所有已加载模块，提供模块查找和遍历功能。
"""


from framework.module.descriptor import ModuleDescriptor


class ModuleRegistry:
    """
    模块注册中心

    单例模式，管理所有已加载的模块。
    """

    _instance: "ModuleRegistry | None" = None
    _modules: dict[str, ModuleDescriptor]

    def __new__(cls) -> "ModuleRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._modules = {}
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置注册中心（主要用于测试）"""
        if cls._instance is not None:
            cls._instance._modules = {}
            cls._instance = None

    def register(self, module: ModuleDescriptor) -> None:
        """
        注册模块

        Args:
            module: 模块描述符实例

        Raises:
            ValueError: 模块名已存在
        """
        if module.name in self._modules:
            raise ValueError(f"Module '{module.name}' already registered")
        self._modules[module.name] = module

    def unregister(self, name: str) -> None:
        """
        注销模块

        Args:
            name: 模块名
        """
        self._modules.pop(name, None)

    def get_module(self, name: str) -> ModuleDescriptor | None:
        """
        获取模块

        Args:
            name: 模块名

        Returns:
            模块描述符实例，不存在返回 None
        """
        return self._modules.get(name)

    def get_all_modules(self) -> list[ModuleDescriptor]:
        """
        获取所有已注册模块

        Returns:
            模块描述符列表
        """
        return list(self._modules.values())

    def get_all_bases(self) -> list[type]:
        """
        获取所有模块的 DeclarativeBase

        Returns:
            DeclarativeBase 列表，用于 Alembic 迁移
        """
        return [module.get_base() for module in self._modules.values()]

    def get_all_schemas(self) -> dict[str, str]:
        """
        获取所有模块的 schema 映射

        Returns:
            {模块名: schema名} 字典
        """
        return {module.name: module.schema for module in self._modules.values()}

    def has_module(self, name: str) -> bool:
        """
        检查模块是否已注册

        Args:
            name: 模块名

        Returns:
            是否已注册
        """
        return name in self._modules

    @property
    def module_names(self) -> list[str]:
        """
        获取所有模块名

        Returns:
            模块名列表
        """
        return list(self._modules.keys())


def get_registry() -> ModuleRegistry:
    """
    获取模块注册中心单例

    Returns:
        ModuleRegistry 实例
    """
    return ModuleRegistry()
