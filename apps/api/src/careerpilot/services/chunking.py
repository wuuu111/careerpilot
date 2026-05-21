from __future__ import annotations

from dataclasses import dataclass

from careerpilot.config import settings
from careerpilot.domain.documents import KnowledgeDocument


@dataclass(slots=True)
class DocumentChunk:
    chunk_index: int
    chunk_text: str
    token_count: int
    metadata: dict[str, object]


class TextChunker:
    def __init__(
        self,
        *,
        target_tokens: int | None = None,
        overlap_tokens: int | None = None,
    ) -> None:
        self.target_tokens = target_tokens or settings.knowledge_chunk_size_tokens
        self.overlap_tokens = (
            settings.knowledge_chunk_overlap_tokens
            if overlap_tokens is None
            else overlap_tokens
        )
        if self.target_tokens <= 0:
            raise ValueError("target_tokens must be greater than zero")
        if self.overlap_tokens < 0 or self.overlap_tokens >= self.target_tokens:
            raise ValueError("overlap_tokens must be between 0 and target_tokens - 1")

    def chunk_document(self, document: KnowledgeDocument) -> list[DocumentChunk]:
        tokens = [token for token in document.embedding_text.split() if token]
        if not tokens:
            return []

        step = self.target_tokens - self.overlap_tokens
        chunks: list[DocumentChunk] = []
        for start in range(0, len(tokens), step):
            window = tokens[start : start + self.target_tokens]
            if not window:
                break
            metadata = dict(document.metadata)
            metadata["chunk_start_token"] = start
            metadata["chunk_end_token"] = start + len(window) - 1
            chunks.append(
                DocumentChunk(
                    chunk_index=len(chunks),
                    chunk_text=" ".join(window),
                    token_count=len(window),
                    metadata=metadata,
                )
            )
            if start + self.target_tokens >= len(tokens):
                break
        return chunks
