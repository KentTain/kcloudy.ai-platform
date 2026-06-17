"""包含检查和验证字典类型方法的工具模块."""


def dict_has_keys_with_types(
    data: dict, expected_fields: list[tuple[str, type]], inplace: bool = False
) -> bool:
    """如果给定的字典包含指定类型的键,则返回True."""
    for field, field_type in expected_fields:
        if field not in data:
            return False

        value = data[field]
        try:
            cast_value = field_type(value)
            if inplace:
                data[field] = cast_value
        except (TypeError, ValueError):
            return False
    return True
