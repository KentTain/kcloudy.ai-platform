"""datashaper专用工具方法模块."""

from typing import cast

from datashaper import TableContainer, VerbInput

_NAMED_INPUTS_REQUIRED = "Named inputs are required"


def get_required_input_table(input: VerbInput, name: str) -> TableContainer:
    """按名称获取必需的输入表."""
    return cast("TableContainer", get_named_input_table(input, name, required=True))


def get_named_input_table(
    input: VerbInput, name: str, required: bool = False
) -> TableContainer | None:
    """从datashaper动词输入中按名称获取输入表."""
    named_inputs = input.named
    if named_inputs is None:
        if not required:
            return None
        raise ValueError(_NAMED_INPUTS_REQUIRED)

    result = named_inputs.get(name)
    if result is None and required:
        msg = f"input '${name}' is required"
        raise ValueError(msg)
    return result
