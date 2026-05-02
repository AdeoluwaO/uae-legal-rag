from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class EmbeddingEngine: 
    """
    Embed a single text string into a vector.
    """
    __model_name = "all-MiniLM-L6-v2"

    def __init__(self):
        self.model = SentenceTransformer(self.__model_name)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Convert multiple texts to vectors.
        
        Input: ["text 1", "text 2", "text 3"]
        Output: [[0.1, 0.2, ...], [0.3, 0.4, ...], ...]
        """

        try: 
            # Remove empty strings 
            valid_texts = [text.strip() for text in texts if text.strip()]

            if not valid_texts:
                print("No valid texts to embed")
                return []
            
            embeddings = self.model.encode(valid_texts)
            return embeddings.tolist()
        except Exception as e:
            print(f"Error embedding texts: {e}")
            return None
    
    def calculate_similarity(self, query_vector: List[float], doc_vector: List[float]) -> float:
        """
        Calculate how similar two vectors are.
        
        Returns: 0.0 to 1.0
            - 1.0 = identical
            - 0.5 = somewhat similar
            - 0.0 = completely different
        """
        if query_vector is None or doc_vector is None:
            print("Error calculating simularity: vectors are None")
            return 0.0
        
        v1 = np.array(query_vector).reshape(1, -1)
        v2 = np.array(doc_vector).reshape(1, -1)

        similarity = cosine_similarity(v1, v2)[0][0]
        return float(similarity)

        
        
