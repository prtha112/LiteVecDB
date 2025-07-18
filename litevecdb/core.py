import os
import time
import json
import pickle
import numpy as np
import zstandard as zstd
from typing import List, Any, Tuple

class LiteVecDB:
    def __init__(self, dim: int, dir_path='vector_store', max_shard_size_mb=5):
        # Initialize the vector database
        self.dim = dim
        self.dir_path = dir_path
        self.max_shard_size = max_shard_size_mb * 1024 * 1024  # MB to bytes
        os.makedirs(self.dir_path, exist_ok=True)
        self.shard_index = self._load_index()

    def _index_path(self):
        # Return the path to the index file
        return os.path.join(self.dir_path, 'index.json')

    def _load_index(self):
        # Load shard index from file if it exists
        if os.path.exists(self._index_path()):
            with open(self._index_path(), 'r') as f:
                return json.load(f)
        return {'last_shard': 0, 'counts': {}}

    def _save_index(self):
        # Save current index state to file
        with open(self._index_path(), 'w') as f:
            json.dump(self.shard_index, f)

    def _get_shard_path(self, shard_id):
        # Construct the path to a specific shard file
        return os.path.join(self.dir_path, f'shard_{shard_id}.pkl.zst')

    def _load_shard(self, shard_id):
        # Load and decompress a shard file using Zstandard
        path = self._get_shard_path(shard_id)
        if os.path.exists(path):
            dctx = zstd.ZstdDecompressor()
            with open(path, 'rb') as f:
                with dctx.stream_reader(f) as decompressor:
                    return pickle.load(decompressor)
        return {'vectors': [], 'metadata': []}

    def _save_shard(self, shard_id, shard_data):
        # Compress and save a shard to disk
        path = self._get_shard_path(shard_id)
        cctx = zstd.ZstdCompressor(level=3) # Compression level (1–22)
        with open(path, 'wb') as f:
            with cctx.stream_writer(f) as compressor:
                pickle.dump(shard_data, compressor)

    def add(self, vector: List[float], meta: Any):
        # Add a new vector and metadata to the latest shard
        shard_id = self.shard_index['last_shard']
        shard_data = self._load_shard(shard_id)

        # Check that the vector matches the expected dimension
        if len(vector) != self.dim:
            raise ValueError(f"Vector dimension mismatch: expected {self.dim}, got {len(vector)}")

        shard_data['vectors'].append(vector)
        shard_data['metadata'].append(meta)
        self._save_shard(shard_id, shard_data)

        # Check if the shard has reached the maximum size
        shard_path = self._get_shard_path(shard_id)
        file_size = os.path.getsize(shard_path)

        if file_size >= self.max_shard_size:
            self.shard_index['last_shard'] = shard_id + 1

        # Update index count and save
        self.shard_index['counts'][str(shard_id)] = len(shard_data['vectors'])
        self._save_index()

    def search(
        self,
        query: List[float],
        k: int = 3,
        metric: str = "cosine",
        filters: dict = None
    ) -> List[Tuple[float, Any]]:
        # Search for top-k most similar vectors using cosine similarity
        if metric != "cosine":
            raise ValueError("Only 'cosine' metric is supported in this version.")
    
        all_results = []
        query_np = np.array(query, dtype='float32')
    
        for shard_id in range(self.shard_index['last_shard'] + 1):
            shard_data = self._load_shard(shard_id)
            if not shard_data['vectors']:
                continue
    
            # Filter vectors by metadata if filters are provided
            filtered = [
                (vec, meta)
                for vec, meta in zip(shard_data['vectors'], shard_data['metadata'])
                if not filters or self._match_filter(meta, filters)
            ]
    
            if not filtered:
                continue
    
            vecs_filtered = np.array([x[0] for x in filtered], dtype='float32')
            metas_filtered = [x[1] for x in filtered]
    
            # Calculate cosine similarity
            sim = self._cosine_similarity(vecs_filtered, query_np)
            top_k_idx = sim.argsort()[::-1][:k]
            for i in top_k_idx:
                all_results.append((float(sim[i]), metas_filtered[i]))
    
        # Sort all results by similarity score and return top-k
        all_results.sort(key=lambda x: x[0], reverse=True)
        return all_results[:k]

    def get_all(self) -> list:
        # Retrieve all vectors and metadata from all shards
        results = []
        for shard_id in range(self.shard_index['last_shard'] + 1):
            shard_data = self._load_shard(shard_id)
            for i in range(len(shard_data['vectors'])):
                results.append({
                    'shard': shard_id,
                    'index': i,
                    'vector': shard_data['vectors'][i],
                    'metadata': shard_data['metadata'][i]
                })
        return results

    def delete(self, shard_id: int, index: int):
        # Delete a specific vector and its metadata from a shard
        shard_data = self._load_shard(shard_id)
        if index < 0 or index >= len(shard_data['vectors']):
            raise IndexError("Index out of range")
        del shard_data['vectors'][index]
        del shard_data['metadata'][index]
        self._save_shard(shard_id, shard_data)
        self.shard_index['counts'][str(shard_id)] = len(shard_data['vectors'])
        self._save_index()

    def delete_all(self):
        # Delete all shards and reset the index
        for shard_id in range(self.shard_index['last_shard'] + 1):
            path = self._get_shard_path(shard_id)
            if os.path.exists(path):
                os.remove(path)
    
        index_path = self._index_path()
        if os.path.exists(index_path):
            os.remove(index_path)
    
        self.shard_index = {'last_shard': 0, 'counts': {}}

    def purge_expired(self):
        # Remove all expired vectors based on metadata expiration timestamp
        purged_count = 0
    
        for shard_id in range(self.shard_index['last_shard'] + 1):
            shard_data = self._load_shard(shard_id)
            if not shard_data['vectors']:
                continue
    
            new_vectors = []
            new_metadata = []
    
            for vec, meta in zip(shard_data['vectors'], shard_data['metadata']):
                if not self._is_expired(meta):
                    new_vectors.append(vec)
                    new_metadata.append(meta)
                else:
                    purged_count += 1
    
            if len(new_vectors) != len(shard_data['vectors']):
                shard_data['vectors'] = new_vectors
                shard_data['metadata'] = new_metadata
                self._save_shard(shard_id, shard_data)
    
            self.shard_index['counts'][str(shard_id)] = len(new_vectors)
    
        self._save_index()
        print(f"Purged {purged_count} expired items.")

    def _cosine_similarity(self, vecs: np.ndarray, query: np.ndarray) -> np.ndarray:
        # Calculate cosine similarity between vectors and a query vector
        vecs_norm = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
        query_norm = query / np.linalg.norm(query)
        return np.dot(vecs_norm, query_norm)

    def _match_filter(self, meta: dict, filters: dict) -> bool:
        # Check if metadata matches the provided filters
        for key, expected_value in filters.items():
            if meta.get(key) != expected_value:
                return False
        return True

    def _is_expired(self, meta: dict) -> bool:
        # Check if the metadata indicates that the item is expired
        expires_at = meta.get("expires_at")
        return expires_at is not None and time.time() >= expires_at