"""索引引擎图提取器声明包根目录."""

from ai.components.graphrag.index.graph.extractors.claims.claim_extractor import (
    ClaimExtractor,
)
from ai.components.graphrag.index.graph.extractors.claims.prompts import (
    CLAIM_EXTRACTION_PROMPT,
)

__all__ = ["CLAIM_EXTRACTION_PROMPT", "ClaimExtractor"]
