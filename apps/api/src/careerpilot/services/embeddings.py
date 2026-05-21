from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol

from careerpilot.config import settings

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


class EmbeddingProvider(Protocol):
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        ...


class DeterministicEmbeddingProvider:
    def __init__(
        self,
        *,
        dimensions: int | None = None,
        namespace: str = "careerpilot-local-v1",
    ) -> None:
        self.dimensions = dimensions or settings.embedding_dimensions
        self.namespace = namespace
        if self.dimensions <= 0:
            raise ValueError("dimensions must be greater than zero")

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = _TOKEN_PATTERN.findall(text.lower())
        if not tokens:
            tokens = text.lower().split()
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.blake2b(
                f"{self.namespace}:{token}".encode(),
                digest_size=16,
            ).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(component * component for component in vector))
        if norm == 0:
            return vector
        return [component / norm for component in vector]


def get_embedding_provider(provider_name: str | None = None) -> EmbeddingProvider:
    name = (provider_name or settings.embedding_provider).lower()
    if name == "local":
        return DeterministicEmbeddingProvider()
    raise ValueError(f"Unsupported embedding provider: {name}")
