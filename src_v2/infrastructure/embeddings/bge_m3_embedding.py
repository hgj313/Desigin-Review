# src_v2/infrastructure/embeddings/bge_m3_embedding.py
"""BGE-M3 embedding service for bilingual text vectorization."""

import logging
from typing import Any

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

from src_v2.domain.ingestion.services import IEmbeddingService

logger = logging.getLogger(__name__)


class BgeM3EmbeddingService(Embeddings, IEmbeddingService):
    """BGE-M3 embedding service for bilingual (Chinese/English) vectorization.

    Uses BAAI/bge-m3 model from sentence-transformers.
    Supports embedding of both single texts and document batches.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cpu",
        normalize_embeddings: bool = True,
    ):
        """Initialize BGE-M3 embedding model.

        Args:
            model_name: HuggingFace model name for BGE-M3.
            device: Device to run model on ("cpu" or "cuda").
            normalize_embeddings: Whether to normalize embeddings to unit length.
        """
        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings

        logger.info(f"Loading BGE-M3 model: {model_name}")
        self._model = SentenceTransformer(model_name, device=device)
        logger.info("BGE-M3 model loaded successfully")

    def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query text.

        Args:
            text: Input text to embed.

        Returns:
            Embedding vector as list of floats.
        """
        embedding = self._model.encode(
            text,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        return embedding.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
            batch_size=32,
            show_progress_bar=len(texts) > 10,
        )
        return [emb.tolist() for emb in embeddings]

    # IEmbeddingService interface
    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        return self.embed_query(text)