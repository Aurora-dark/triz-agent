#!/usr/bin/env python
"""
一键初始化完整系统
运行: python scripts/setup_system.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import TRIZDatabase
from src.vector_store import VectorStore

def main():
    print("="*60)
    print(" TRIZ知识系统 - 一键初始化")
    print("="*60)
    
    # 步骤1: 导入数据
    print("\n[1/3] 导入JSON数据到数据库...")
    from scripts.import_data import main as import_main
    import_main()
    
    # 步骤2: 构建向量索引
    print("\n[2/3] 构建FAISS向量索引...")
    from scripts.build_vector_index import main as build_main
    build_main()
    
    # 步骤3: 验证系统
    print("\n[3/3] 验证系统...")
    db = TRIZDatabase()
    params = db.get_all_parameters()
    principles = db.get_all_principles()
    
    print(f"    数据库: {len(params)} 参数, {len(principles)} 原理")
    
    # 测试检索
    vector_store = VectorStore()
    try:
        vector_store.load()
        test_result = vector_store.search("测试", top_k=1)
        print(f"    向量库: 已加载，共 {vector_store.index.ntotal} 条向量")
    except Exception as e:
        print(f"    向量库: {e}")
    
    print("\n" + "="*60)
    print(" 系统初始化完成！")
    print("="*60)
    print("\n下一步:")
    print("   python scripts/test_system.py     # 运行功能测试")
    print("   python quick_start.py              # 启动交互式解题")

if __name__ == "__main__":
    main()