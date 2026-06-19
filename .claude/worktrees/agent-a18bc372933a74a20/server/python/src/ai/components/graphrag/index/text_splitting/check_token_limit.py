"""Token 限制方法定义."""

from ai.components.graphrag.index.text_splitting.text_splitting import (
    TokenTextSplitter,
)


def check_token_limit(text, max_token):
    """检查 token 限制."""
    text_splitter = TokenTextSplitter(chunk_size=max_token, chunk_overlap=0)
    docs = text_splitter.split_text(text)
    if len(docs) > 1:
        return 0
    return 1
