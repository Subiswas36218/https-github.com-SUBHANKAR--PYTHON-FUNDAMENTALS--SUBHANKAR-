import numpy as np
from google import genai
from google.genai import types
from sklearn.metrics.pairwise import cosine_similarity

client = genai.Client()

result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=[
        "proton collision",
        "proton collision happens in LHC",
        "proton collision is an operation between two protons",
        "New Delhi is the capital of India",
    ],
    config=types.EmbedContentConfig(
        output_dimensionality=768,
        task_type="SEMANTIC_SIMILARITY",
    ),
)

embeddings_matrix = np.array(
    [np.array(embedding.values) for embedding in result.embeddings]
)

similarity_matrix = cosine_similarity(embeddings_matrix)

print(similarity_matrix)
