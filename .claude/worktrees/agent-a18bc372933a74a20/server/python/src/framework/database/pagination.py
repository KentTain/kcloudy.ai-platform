"""
分页信息类

提供分页相关的信息封装。
"""


class Pagination:
    """
    分页信息类

    提供分页相关信息的简单类，包括：
    - 当前页码
    - 每页记录数
    - 总记录数
    - 总页数
    """

    def __init__(self, page: int, page_size: int, total: int, total_page: int):
        self.page = page
        self.page_size = page_size
        self.total = total
        self.total_page = total_page

    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.page < self.total_page

    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.page > 1

    def to_dict(self) -> dict[str, int]:
        """转换为字典"""
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total": self.total,
            "total_page": self.total_page,
        }