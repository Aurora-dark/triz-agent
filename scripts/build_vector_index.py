#!/usr/bin/env python
"""
构建FAISS向量索引
运行: python scripts/build_vector_index.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import TRIZDatabase
from src.vector_store import VectorStore

def main():
    print("🚀 构建FAISS向量索引...")
    
    db = TRIZDatabase()
    
    # 获取数据
    params = db.get_all_parameters()
    principles = db.get_all_principles()
    
    print(f"📊 参数: {len(params)} 条")
    print(f"📊 原理: {len(principles)} 条")
    
    if len(params) == 0:
        print("❌ 参数表为空，请先运行 import_data.py")
        return
    
    # 构建向量索引
    print("\n🔢 生成向量...")
    vector_store = VectorStore()
    vector_store.build_vectors(params, principles)  # ← 确保方法名是 build_vectors
    vector_store.save()
    
    # 测试检索
    print("\n" + "="*50)
    print("🧪 测试检索")
    print("="*50)
    
    test_queries = [
        "零件太重了，搬不动",
        "如何让产品更坚固耐用",
        "局部强化处理"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Q: {query}")
        results = vector_store.search(query, top_k=3)
        for r in results:
            type_icon = "📊" if r['type'] == 'parameter' else "💡"
            print(f"   {type_icon} [{r['type']}] {r['name']} (相似度: {r['similarity']:.3f})")
    
    print("\n✅ 向量索引构建完成！")

if __name__ == "__main__":
    main()