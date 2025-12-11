import numpy as np
from google import genai
from google.genai import types

client = genai.Client()


def embed(text: str, task_type: str = "SEMANTIC_SIMILARITY") -> np.ndarray:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=[text],
        config=types.EmbedContentConfig(
            output_dimensionality=768,
            task_type=task_type,
        ),
    )
    if result.embeddings is None:
        raise ValueError

    return np.array(result.embeddings[0].values)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


query = embed("What is the capital of India?", task_type="RETRIEVAL_QUERY")
a = embed("New Delhi is the capital of India.", task_type="RETRIEVAL_DOCUMENT")
b = embed("Moscow is the capital of Russia.", task_type="RETRIEVAL_DOCUMENT")

print("Cosine similarity:", cosine_similarity(query, a), cosine_similarity(query, b))
