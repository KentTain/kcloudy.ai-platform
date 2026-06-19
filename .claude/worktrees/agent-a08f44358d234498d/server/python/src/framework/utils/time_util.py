"""
时间日期工具函数
"""

from datetime import datetime, timedelta
from typing import Optional


def format_datetime(
    dt: datetime,
    fmt: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    格式化日期时间

    Args:
        dt: datetime 对象
        fmt: 格式字符串

    Returns:
        str: 格式化后的字符串
    """
    if dt is None:
        return ""
    return dt.strftime(fmt)


def parse_datetime(
    text: str,
    fmt: str = "%Y-%m-%d %H:%M:%S"
) -> Optional[datetime]:
    """
    解析日期时间字符串

    Args:
        text: 日期时间字符串
        fmt: 格式字符串

    Returns:
        datetime: 解析后的 datetime 对象
    """
    if not text:
        return None

    try:
        return datetime.strptime(text, fmt)
    except ValueError:
        return None


def timestamp_to_datetime(timestamp: int | float) -> datetime:
    """
    时间戳转 datetime

    Args:
        timestamp: 时间戳（秒或毫秒）

    Returns:
        datetime: datetime 对象
    """
    # 判断是秒级还是毫秒级时间戳
    if timestamp > 1e10:
        timestamp = timestamp / 1000

    return datetime.fromtimestamp(timestamp)


def datetime_to_timestamp(dt: datetime, milliseconds: bool = False) -> int:
    """
    datetime 转时间戳

    Args:
        dt: datetime 对象
        milliseconds: 是否返回毫秒级时间戳

    Returns:
        int: 时间戳
    """
    ts = int(dt.timestamp())
    return ts * 1000 if milliseconds else ts


def humanize_time(dt: datetime, now: Optional[datetime] = None) -> str:
    """
    人性化时间显示

    Args:
        dt: 目标时间
        now: 当前时间（默认使用当前系统时间）

    Returns:
        str: 人性化时间字符串，如 "3 小时前"
    """
    if dt is None:
        return ""

    if now is None:
        now = datetime.now()

    diff = now - dt

    if diff < timedelta(seconds=60):
        return "刚刚"
    elif diff < timedelta(hours=1):
        return f"{int(diff.seconds / 60)} 分钟前"
    elif diff < timedelta(days=1):
        return f"{int(diff.seconds / 3600)} 小时前"
    elif diff < timedelta(days=30):
        return f"{diff.days} 天前"
    elif diff < timedelta(days=365):
        months = int(diff.days / 30)
        return f"{months} 个月前"
    else:
        years = int(diff.days / 365)
        return f"{years} 年前"


def get_time_range(range_type: str, base: Optional[datetime] = None) -> tuple[datetime, datetime]:
    """
    获取时间范围

    Args:
        range_type: 范围类型（today/yesterday/week/month/year）
        base: 基准时间（默认使用当前时间）

    Returns:
        tuple: (开始时间, 结束时间)
    """
    if base is None:
        base = datetime.now()

    if range_type == "today":
        start = base.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif range_type == "yesterday":
        start = (base - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif range_type == "week":
        start = (base - timedelta(days=base.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
    elif range_type == "month":
        start = base.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if base.month == 12:
            end = start.replace(year=base.year + 1, month=1)
        else:
            end = start.replace(month=base.month + 1)
    elif range_type == "year":
        start = base.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=base.year + 1)
    else:
        raise ValueError(f"不支持的时间范围类型: {range_type}")

    return start, end
