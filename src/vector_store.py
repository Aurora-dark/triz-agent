"""
FAISS向量库 - 支持参数+原理混合检索
"""
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional

class VectorStore:
    """FAISS向量存储管理器"""
    
    def __init__(self, model_name="BAAI/bge-small-zh-v1.5", index_path="models/faiss_index"):
        self.model_name = model_name
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.index = None
        self.id_map = []
    
    def load_model(self):
        """加载Embedding模型"""
        if self.model is None:
            print(f"📥 加载模型: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
        return self.model
    
    def build_vectors(self, parameters: List[dict], principles: List[dict]):
        """
        构建参数+原理的混合向量索引
        """
        self.load_model()
        
        # 构建语料
        items = []
        corpus = []
        
        # 1. 添加参数
        for p in parameters:
            text = f"参数名称: {p.get('name_cn', '')}。定义: {p.get('desc_cn', '')}"
            corpus.append(text)
            items.append({
                'id': p['id'],
                'type': 'parameter',
                'name': p.get('name_cn', ''),
                'description': p.get('desc_cn', '')
            })
        
        # 2. 添加原理
        for prin in principles:
            text = f"发明原理: {prin.get('name_cn', '')}。解释: {prin.get('explain_cn', '')}。案例: {prin.get('case_cn', '')}"
            corpus.append(text)
            items.append({
                'id': prin['id'],
                'type': 'principle',
                'name': prin.get('name_cn', ''),
                'description': prin.get('explain_cn', '')
            })
        
        print(f"🔢 生成 {len(corpus)} 条向量（{len(parameters)}参数 + {len(principles)}原理）")
        embeddings = self.model.encode(corpus, normalize_embeddings=True)
        
        # 创建FAISS索引
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings.astype('float32'))
        
        # 保存ID映射
        self.id_map = items
        
        print(f"✅ 向量索引构建完成，维度: {dimension}")
        return self.index
    
    def save(self, name="triz_hybrid"):
        """保存索引到磁盘"""
        if self.index is None:
            raise ValueError("索引未构建，请先调用 build_vectors()")
        
        index_file = self.index_path / f"{name}.index"
        map_file = self.index_path / f"{name}_map.json"
        
        faiss.write_index(self.index, str(index_file))
        with open(map_file, 'w', encoding='utf-8') as f:
            json.dump(self.id_map, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 索引已保存: {index_file}")
    
    def load(self, name="triz_hybrid"):
        """从磁盘加载索引"""
        index_file = self.index_path / f"{name}.index"
        map_file = self.index_path / f"{name}_map.json"
        
        if not index_file.exists():
            raise FileNotFoundError(f"索引文件不存在: {index_file}")
        
        self.load_model()
        self.index = faiss.read_index(str(index_file))
        with open(map_file, 'r', encoding='utf-8') as f:
            self.id_map = json.load(f)
        
        print(f"✅ 加载索引成功，共 {self.index.ntotal} 条向量")
        return self.index
    
    def search(self, query: str, top_k: int = 5, type_filter: Optional[str] = None) -> List[Dict]:
        """
        语义检索
        type_filter: 'parameter' 只检索参数, 'principle' 只检索原理
        """
        if self.index is None:
            raise ValueError("索引未加载，请先调用 load()")
        
        query_vec = self.model.encode([query], normalize_embeddings=True)
        distances, indices = self.index.search(query_vec.astype('float32'), top_k * 2)
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx >= 0 and idx < len(self.id_map):
                item = self.id_map[idx].copy()
                if type_filter and item.get('type') != type_filter:
                    continue
                item['similarity'] = float(dist)
                results.append(item)
                if len(results) >= top_k:
                    break
        
        return results