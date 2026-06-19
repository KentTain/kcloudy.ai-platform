"""
GPT-2 Tokenizer

迁移自 Alon: src/alon/components/model/model_providers/__base__/tokenizers/gpt2_tokenizer.py

使用 GPT-2 tokenizer 进行本地 token 计数
"""

import tiktoken


class GPT2Tokenizer:
    """GPT-2 Tokenizer 类，用于本地 token 计数"""

    _encoding = None

    @classmethod
    def _get_encoding(cls):
        """获取或创建 GPT-2 编码器实例"""
        if cls._encoding is None:
            cls._encoding = tiktoken.encoding_for_model("gpt2")
        return cls._encoding

    @classmethod
    def get_num_tokens(cls, text: str) -> int:
        """
        使用 GPT-2 计算给定文本的 token 数量

        :param text: 要计算 token 数量的文本
        :return: token 数量
        """
        # 优化：为了避免性能问题，不计算过长文本的 token 数量
        # 仅保证文本长度小于 100000
        if len(text) >= 100000:
            return len(text)

        encoding = cls._get_encoding()
        return len(encoding.encode(text))

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        """
        将文本分割为 token 列表

        :param text: 要分割的文本
        :return: token 列表
        """
        encoding = cls._get_encoding()
        return [encoding.decode([token]) for token in encoding.encode(text)]
