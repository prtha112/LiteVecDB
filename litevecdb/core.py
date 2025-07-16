import os
import json
import pickle
import numpy as np
import zstandard as zstd
from typing import List, Any, Tuple

class LiteVecDB:
    def __init__(self, dim: int, dir_path='vector_store', max_shard_size_mb=5):
        self.dim = dim
        self.dir_path = dir_path
        self.max_shard_size = max_shard_size_mb * 1024 * 1024  # MB to bytes
        os.makedirs(self.dir_path, exist_ok=True)
        self.shard_index = self._load_index()

    def _index_path(self):
        return os.path.join(self.dir_path, 'index.json')

    def _load_index(self):
        if os.path.exists(self._index_path()):
            with open(self._index_path(), 'r') as f:
                return json.load(f)
        return {'last_shard': 0, 'counts': {}}

    def _save_index(self):
        with open(self._index_path(), 'w') as f:
            json.dump(self.shard_index, f)

    def _get_shard_path(self, shard_id):
        return os.path.join(self.dir_path, f'shard_{shard_id}.pkl.zst')

    def _load_shard(self, shard_id):
        path = self._get_shard_path(shard_id)
        if os.path.exists(path):
            dctx = zstd.ZstdDecompressor()
            with open(path, 'rb') as f:
                with dctx.stream_reader(f) as decompressor:
                    return pickle.load(decompressor)
        return {'vectors': [], 'metadata': []}

    def _save_shard(self, shard_id, shard_data):
        path = self._get_shard_path(shard_id)
        cctx = zstd.ZstdCompressor(level=3)  # ระดับ compression (1–22)
        with open(path, 'wb') as f:
            with cctx.stream_writer(f) as compressor:
                pickle.dump(shard_data, compressor)

    def add(self, vector: List[float], meta: Any):
        shard_id = self.shard_index['last_shard']
        shard_data = self._load_shard(shard_id)

        # Validate dimension
        if len(vector) != self.dim:
            raise ValueError(f"Vector dimension mismatch: expected {self.dim}, got {len(vector)}")

        shard_data['vectors'].append(vector)
        shard_data['metadata'].append(meta)
        self._save_shard(shard_id, shard_data)

        # Check shard file size
        shard_path = self._get_shard_path(shard_id)
        file_size = os.path.getsize(shard_path)

        if file_size >= self.max_shard_size:
            self.shard_index['last_shard'] = shard_id + 1

        self.shard_index['counts'][str(shard_id)] = len(shard_data['vectors'])
        self._save_index()

    def search(self, query: List[float], k=3, metric="l2") -> List[Tuple[float, Any]]:
        all_results = []
        query_np = np.array(query, dtype='float32')
    
        for shard_id in range(self.shard_index['last_shard'] + 1):
            shard_data = self._load_shard(shard_id)
            if not shard_data['vectors']:
                continue
    
            vectors = np.array(shard_data['vectors'], dtype='float32')
    
            if metric == "cosine":
                sim = self._cosine_similarity(vectors, query_np)
                top_k_idx = sim.argsort()[::-1][:k]  # reverse → highest first
                for i in top_k_idx:
                    all_results.append((float(sim[i]), shard_data['metadata'][i]))
            else:  # default: l2
                distances = np.linalg.norm(vectors - query_np, axis=1)
                top_k_idx = distances.argsort()[:k]
                for i in top_k_idx:
                    all_results.append((float(distances[i]), shard_data['metadata'][i]))

        if metric == "cosine":
            all_results.sort(key=lambda x: x[0], reverse=True)
        else:
            all_results.sort(key=lambda x: x[0])
    
        return all_results[:k]


    def get_all(self) -> list:
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
        shard_data = self._load_shard(shard_id)
        if index < 0 or index >= len(shard_data['vectors']):
            raise IndexError("Index out of range")
        del shard_data['vectors'][index]
        del shard_data['metadata'][index]
        self._save_shard(shard_id, shard_data)
        self.shard_index['counts'][str(shard_id)] = len(shard_data['vectors'])
        self._save_index()

    def delete_all(self):
        for shard_id in range(self.shard_index['last_shard'] + 1):
            path = self._get_shard_path(shard_id)
            if os.path.exists(path):
                os.remove(path)
    
        index_path = self._index_path()
        if os.path.exists(index_path):
            os.remove(index_path)
    
        self.shard_index = {'last_shard': 0, 'counts': {}}

    def _cosine_similarity(self, vecs: np.ndarray, query: np.ndarray) -> np.ndarray:
        vecs_norm = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
        query_norm = query / np.linalg.norm(query)
        return np.dot(vecs_norm, query_norm)