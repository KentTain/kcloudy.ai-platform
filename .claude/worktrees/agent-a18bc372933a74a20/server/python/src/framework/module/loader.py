"""
模块加载器

实现模块扫描、依赖解析和拓扑排序。
"""

import importlib.util
from pathlib import Path
from typing import Any

from framework.module.descriptor import ModuleDescriptor
from framework.module.registry import ModuleRegistry, get_registry


class CyclicDependencyError(Exception):
    """循环依赖异常"""

    def __init__(self, cycle: list[str]):
        self.cycle = cycle
        super().__init__(f"Cyclic dependency detected: {' -> '.join(cycle)}")


class ModuleLoadError(Exception):
    """模块加载异常"""

    pass


def discover_modules(src_path: Path) -> list[ModuleDescriptor]:
    """
    扫描源码目录发现所有模块

    扫描 src/*/module.py 文件，加载模块描述符。

    Args:
        src_path: src 目录路径

    Returns:
        模块描述符列表
    """
    modules: list[ModuleDescriptor] = []

    if not src_path.exists():
        return modules

    for module_dir in src_path.iterdir():
        if not module_dir.is_dir():
            continue

        # 跳过非模块目录（如 __pycache__）
        if module_dir.name.startswith("_"):
            continue

        module_file = module_dir / "module.py"
        if not module_file.exists():
            continue

        # 动态加载 module.py
        module_name = module_dir.name
        spec = importlib.util.spec_from_file_location(
            f"src.{module_name}.module",
            module_file
        )
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 查找 ModuleDescriptor 实例
        # 约定：module.py 中定义名为 {ModuleName}Module 的类
        class_name = f"{module_name.capitalize()}Module"
        descriptor_class = getattr(module, class_name, None)

        if descriptor_class is None:
            # 尝试查找任何以 Module 结尾的类
            for attr_name in dir(module):
                if attr_name.endswith("Module") and attr_name != "ModuleDescriptor":
                    descriptor_class = getattr(module, attr_name)
                    break

        if descriptor_class is not None:
            try:
                descriptor = descriptor_class()
                modules.append(descriptor)
            except Exception as e:
                raise ModuleLoadError(
                    f"Failed to instantiate module descriptor '{class_name}' "
                    f"in {module_file}: {e}"
                ) from e

    return modules


def resolve_dependencies(modules: list[ModuleDescriptor]) -> list[ModuleDescriptor]:
    """
    解析模块依赖并拓扑排序

    确保依赖模块先于依赖它的模块加载。

    Args:
        modules: 模块描述符列表

    Returns:
        排序后的模块列表

    Raises:
        CyclicDependencyError: 存在循环依赖
        ValueError: 依赖的模块不存在
    """
    # 构建模块名到模块的映射
    name_to_module: dict[str, ModuleDescriptor] = {
        m.name: m for m in modules
    }

    # 构建依赖图
    in_degree: dict[str, int] = {m.name: 0 for m in modules}
    dependents: dict[str, list[str]] = {m.name: [] for m in modules}

    for module in modules:
        for dep in module.dependencies:
            if dep not in name_to_module:
                raise ValueError(
                    f"Module '{module.name}' depends on '{dep}', "
                    f"but '{dep}' is not available"
                )
            in_degree[module.name] += 1
            dependents[dep].append(module.name)

    # Kahn's 算法拓扑排序
    result: list[ModuleDescriptor] = []
    queue: list[str] = [name for name, degree in in_degree.items() if degree == 0]

    while queue:
        # 按名称排序确保确定性
        queue.sort()
        name = queue.pop(0)
        result.append(name_to_module[name])

        for dependent in dependents[name]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    # 检测循环依赖
    if len(result) != len(modules):
        # 找到循环依赖的模块
        cycle_modules = [m for m in modules if m.name not in [r.name for r in result]]
        cycle_names = [m.name for m in cycle_modules]
        raise CyclicDependencyError(cycle_names + [cycle_names[0]])

    return result


def filter_modules(
    modules: list[ModuleDescriptor],
    module_names: list[str] | None
) -> list[ModuleDescriptor]:
    """
    按名称过滤模块

    Args:
        modules: 模块描述符列表
        module_names: 要加载的模块名列表，None 表示加载全部

    Returns:
        过滤后的模块列表

    Raises:
        ValueError: 指定的模块名不存在
    """
    if module_names is None:
        return modules

    name_set = set(module_names)
    result: list[ModuleDescriptor] = []

    for module in modules:
        if module.name in name_set:
            result.append(module)
            name_set.discard(module.name)

    if name_set:
        raise ValueError(f"Modules not found: {', '.join(name_set)}")

    return result


def load_modules(
    src_path: Path,
    module_names: list[str] | None = None,
    registry: ModuleRegistry | None = None
) -> list[ModuleDescriptor]:
    """
    加载模块的完整流程

    1. 扫描模块目录
    2. 按名称过滤
    3. 解析依赖并排序
    4. 注册到注册中心

    Args:
        src_path: src 目录路径
        module_names: 要加载的模块名列表，None 表示加载全部
        registry: 模块注册中心，None 则使用全局单例

    Returns:
        加载完成的模块列表（已排序）

    Raises:
        CyclicDependencyError: 存在循环依赖
        ModuleLoadError: 模块加载失败
        ValueError: 指定的模块名不存在
    """
    if registry is None:
        registry = get_registry()

    # 1. 扫描模块
    modules = discover_modules(src_path)

    # 2. 按名称过滤
    modules = filter_modules(modules, module_names)

    # 3. 解析依赖并排序
    modules = resolve_dependencies(modules)

    # 4. 注册到注册中心
    for module in modules:
        registry.register(module)

    return modules
