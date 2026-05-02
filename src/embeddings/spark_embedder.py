# PySpark UDF for Distributed Embeddings
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import ArrayType, FloatType
import pandas as pd
from sentence_transformers import SentenceTransformer
import torch
import logging

logger = logging.getLogger(__name__)

# Module-level cache so each Spark executor process loads the model only once,
# rather than reloading it for every partition (key teaching point for students).
_MODEL_CACHE: dict = {}


class SparkEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None  # driver-side model (for embed_batch)

    @property
    def model(self):
        """Backward-compatible alias used by some tests/docs."""
        return self._model

    # ------------------------------------------------------------------ #
    # Driver-side helpers                                                  #
    # ------------------------------------------------------------------ #

    def load_model(self) -> SentenceTransformer:
        """Load model on the driver (used by embed_batch)."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
            if torch.cuda.is_available():
                self._model = self._model.to("cuda")
                logger.info("Driver model loaded on GPU")
            else:
                logger.info("Driver model loaded on CPU")
        return self._model

    def embed_batch(self, texts: list) -> list:
        """Embed texts on the driver — for small ad-hoc queries / testing."""
        model = self.load_model()
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=len(texts) > 10,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    # ------------------------------------------------------------------ #
    # Distributed UDF                                                      #
    # ------------------------------------------------------------------ #

    def get_embedding_udf(self):
        """
        Return a Pandas UDF for distributed embedding generation.

        IMPORTANT (teaching point):
        - We capture only `model_name` (a string), NOT the SentenceTransformer
          object. Capturing the object would pickle it and ship it over the
          network to every executor — very slow and fragile.
        - Instead, each executor worker process loads the model lazily on first
          call and caches it in `_MODEL_CACHE` for the lifetime of the process.
          Subsequent partitions on the same executor reuse the cached model.
        - On a real GPU cluster, set CUDA_VISIBLE_DEVICES per-executor via
          spark.executorEnv.CUDA_VISIBLE_DEVICES or ResourceRequest.
        """
        model_name = self.model_name  # capture only the name

        @pandas_udf(ArrayType(FloatType()))
        def embed_texts(texts: pd.Series) -> pd.Series:
            # Lazy per-process model loading (GPU-aware)
            if model_name not in _MODEL_CACHE:
                m = SentenceTransformer(model_name)
                if torch.cuda.is_available():
                    m = m.to("cuda")
                _MODEL_CACHE[model_name] = m
                logger.info("Executor loaded model: %s", model_name)

            model = _MODEL_CACHE[model_name]
            embeddings = model.encode(
                texts.tolist(),
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            return pd.Series(embeddings.tolist())

        return embed_texts
