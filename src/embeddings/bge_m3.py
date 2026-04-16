"""bge-m3 embedding model wrapper.

Provides a LangChain-compatible interface to the BAAI/bge-m3 model
for bilingual Chinese/English embeddings at 1024 dimensions.

References:
- D-04: Model bge-m3 with 1024 dimensions
- D-05: Batch size 64
- D-11: Support Chinese/English cross-lingual retrieval
"""

import logging
from typing import List

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


class BGE_M3_Embeddings(Embeddings):
    """bge-m3 embedding wrapper per D-04, D-05, D-11.

    Model: BAAI/bge-m3
    Dimensions: 1024
    Batch size: 64
    Normalize: True (cosine similarity compatible)
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        batch_size: int = 64,
        normalize: bool = True,
    ):
        """Initialize bge-m3 embedding model.

        Args:
            model_name: HuggingFace model name (default BAAI/bge-m3).
            batch_size: Batch size for embedding generation (default 64 per D-05).
            normalize: Whether to normalize embeddings (default True for cosine similarity).
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.normalize = normalize

        # Load the sentence transformer model
        self.model = SentenceTransformer(model_name)

        # Verify embedding dimension is 1024
        test_embedding = self.model.encode("test")
        dimension = len(test_embedding)
        if dimension != 1024:
            logging.warning(
                f"bge-m3 embedding dimension is {dimension}, expected 1024"
            )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts with batch_size=64 (D-05).

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (1024-dimensional).
        """
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=len(texts) > 10,  # Show progress for large batches
            normalize_embeddings=self.normalize,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text.

        Args:
            text: Query string to embed.

        Returns:
            Single embedding vector (1024-dimensional).
        """
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,  # Always normalize queries
        )
        return embedding.tolist()


# Usage example (commented out for reference):
# embeddings = BGE_M3_Embeddings(batch_size=64)  # D-05
# doc_embeddings = embeddings.embed_documents(["text1", "text2"])
# query_embedding = embeddings.embed_query("query text")


__all__ = ["BGE_M3_Embeddings"]
