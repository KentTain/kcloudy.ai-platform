"""包含 run, _translate_text and _create_translation_prompt methods definition."""

import logging
import traceback
from typing import Any

from datashaper import VerbCallbacks

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.enums import LLMType
from ai.components.graphrag.index.cache import PipelineCache
from ai.components.graphrag.index.llm import load_llm
from ai.components.graphrag.index.text_splitting import TokenTextSplitter
from ai.components.graphrag.index.verbs.text.translate.strategies.defaults import (
    TRANSLATION_PROMPT as DEFAULT_TRANSLATION_PROMPT,
)
from ai.components.graphrag.index.verbs.text.translate.strategies.typing import (
    TextTranslationResult,
)
from ai.components.graphrag.llm import CompletionLLM

log = logging.getLogger(__name__)


async def run(
    input: str | list[str],
    args: dict[str, Any],
    callbacks: VerbCallbacks,
    pipeline_cache: PipelineCache,
) -> TextTranslationResult:
    """
    执行run。

    Args:
        input (str | list[str]): input 参数。
        args (dict[str, Any]): args 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        pipeline_cache (PipelineCache): pipeline_cache 参数。

    Returns:
        处理结果。
    """
    llm_config = args.get("llm", {"type": LLMType.StaticResponse})
    llm_type = llm_config.get("type", LLMType.StaticResponse)
    llm = load_llm(
        "text_translation",
        llm_type,
        callbacks,
        pipeline_cache,
        llm_config,
        chat_only=True,
    )
    language = args.get("language", "English")
    prompt = args.get("prompt")
    chunk_size = args.get("chunk_size", defs.CHUNK_SIZE)
    chunk_overlap = args.get("chunk_overlap", defs.CHUNK_OVERLAP)

    input = [input] if isinstance(input, str) else input
    return TextTranslationResult(
        translations=[
            await _translate_text(
                text, language, prompt, llm, chunk_size, chunk_overlap, callbacks
            )
            for text in input
        ]
    )


async def _translate_text(
    text: str,
    language: str,
    prompt: str | None,
    llm: CompletionLLM,
    chunk_size: int,
    chunk_overlap: int,
    callbacks: VerbCallbacks,
) -> str:
    """
    翻译translate_text。

    Args:
        text (str): text 参数。
        language (str): language 参数。
        prompt (str | None): prompt 参数。
        llm (CompletionLLM): llm 参数。
        chunk_size (int): chunk_size 参数。
        chunk_overlap (int): chunk_overlap 参数。
        callbacks (VerbCallbacks): callbacks 参数。

    Returns:
        处理结果。
    """
    splitter = TokenTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    out = ""
    chunks = splitter.split_text(text)
    for chunk in chunks:
        try:
            result = await llm(
                chunk,
                history=[
                    {
                        "role": "system",
                        "content": (prompt or DEFAULT_TRANSLATION_PROMPT),
                    }
                ],
                variables={"language": language},
            )
            out += result.output or ""
        except Exception as e:
            log.exception("error translating text")
            callbacks.error("Error translating text", e, traceback.format_exc())
            out += ""

    return out
