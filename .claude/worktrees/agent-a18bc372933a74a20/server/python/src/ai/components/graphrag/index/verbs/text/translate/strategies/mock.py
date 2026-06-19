"""包含 run and _summarize_text methods definitions."""

from typing import Any

from datashaper import VerbCallbacks

from ai.components.graphrag.index.cache import PipelineCache
from ai.components.graphrag.index.verbs.text.translate.strategies.typing import (
    TextTranslationResult,
)


async def run(
    input: str | list[str],
    _args: dict[str, Any],
    _reporter: VerbCallbacks,
    _cache: PipelineCache,
) -> TextTranslationResult:
    """
    执行run。

    Args:
        input (str | list[str]): input 参数。
        _args (dict[str, Any]): _args 参数。
        _reporter (VerbCallbacks): _reporter 参数。
        _cache (PipelineCache): _cache 参数。

    Returns:
        处理结果。
    """
    input = [input] if isinstance(input, str) else input
    return TextTranslationResult(translations=[_translate_text(text) for text in input])


def _translate_text(text: str) -> str:
    """
    翻译translate_text。

    Args:
        text (str): text 参数。

    Returns:
        处理结果。
    """
    return f"{text} translated"
