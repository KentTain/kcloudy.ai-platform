"""
枚举工具函数
"""

import threading
from copy import deepcopy

from framework.common.enums import EnumMemberData


class EnumDataUtils:
    """工具类：用于统一管理、缓存和获取枚举数据"""

    # 用于分隔多个枚举类型的分隔符
    COMMA = ","
    # 存储所有枚举类型数据的映射表，键为枚举类型名称，值为枚举成员数据列表
    ENUM_MAP: dict[str, list[EnumMemberData]] = {}
    # 标记枚举数据是否已初始化
    _initialized = False
    # 线程锁，用于确保枚举数据初始化的线程安全
    _lock = threading.Lock()

    def __init__(self):
        """禁止实例化此工具类

        此类设计为静态工具类，不应被实例化
        """
        raise TypeError("This class is not instantiable")

    @staticmethod
    def _init_enums():
        """初始化所有枚举数据

        此方法使用双重检查锁定模式确保线程安全地初始化枚举数据。
        只有在第一次调用时才会执行初始化，后续调用将直接返回。
        动态获取 models/enums.py 中的所有枚举类型。
        """
        if EnumDataUtils._initialized:
            return

        with EnumDataUtils._lock:
            if EnumDataUtils._initialized:
                return

            import inspect

            # 获取 enums.py 中的所有枚举类
            from demo.models import enums
            from demo.models.enums import EnumBase

            for name, cls in inspect.getmembers(enums):
                if (
                    inspect.isclass(cls)
                    and issubclass(cls, EnumBase)
                    and cls != EnumBase
                ):
                    EnumDataUtils.ENUM_MAP[name] = cls.get_enum_list()

            EnumDataUtils._initialized = True

    @staticmethod
    def get_enum_data(enum_type: str) -> list[EnumMemberData] | None:
        """获取指定类型的枚举数据

        :param enum_type: 枚举类型名称
        :return: 指定类型的枚举成员数据列表，如果类型不存在则返回 None
        """
        EnumDataUtils._init_enums()
        return EnumDataUtils.ENUM_MAP.get(enum_type)

    @staticmethod
    def get_batch_enum_data(types: str) -> dict[str, list[EnumMemberData] | None]:
        """批量获取多个枚举类型的数据

        :param types: 以逗号分隔的多个枚举类型名称
        :return: 包含所有请求的枚举类型数据的字典，键为枚举类型名称，值为对应的枚举成员数据列表
        """
        EnumDataUtils._init_enums()
        result_map = {}
        for enum_type in types.split(EnumDataUtils.COMMA):
            key = enum_type.strip()
            result_map[key] = EnumDataUtils.ENUM_MAP.get(key)
        return result_map

    @staticmethod
    def get_all_enum_data() -> dict[str, list[EnumMemberData]]:
        """获取所有枚举类型的数据

        :return: 所有枚举类型数据的深拷贝，避免外部修改影响内部缓存
        """
        EnumDataUtils._init_enums()
        return deepcopy(EnumDataUtils.ENUM_MAP)

    @staticmethod
    def to_enum(enum_class, value):
        """将给定的值转换为指定枚举类的成员

        :param enum_class: 目标枚举类
        :param value: 要转换的值，可以是枚举成员、枚举名称或枚举值
        :return: 对应的枚举成员
        :raises ValueError: 如果无法将值转换为有效的枚举成员
        """
        if isinstance(value, enum_class):
            return value
        if isinstance(value, str):
            try:
                return enum_class[value]
            except KeyError:
                for member in enum_class:
                    if member.value == value:
                        return member
        raise ValueError(f"{value} is not a valid value of {enum_class.__name__}")
