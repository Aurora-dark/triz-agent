#!/usr/bin/env python
"""
从分开的JSON文件导入TRIZ数据
运行: python scripts/import_data.py
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import TRIZDatabase

def main():
    print(" 导入TRIZ数据...")
    
    db = TRIZDatabase()
    
    # 文件路径
    data_dir = Path("data/raw")
    param_file = data_dir / "triz_parameters.json"
    principle_file = data_dir / "triz_principles.json"
    matrix_file = data_dir / "triz_matrix.json"
    
    # 检查文件是否存在
    if not param_file.exists():
        print(f" 参数文件不存在: {param_file}")
        print("请先重命名文件添加 .json 扩展名")
        return
    
    if not principle_file.exists():
        print(f" 原理文件不存在: {principle_file}")
        return
    
    if not matrix_file.exists():
        print(f" 矩阵文件不存在: {matrix_file}")
        return
    
    # 导入数据
    print("\n 导入参数...")
    db.import_parameters_from_json(param_file)
    
    print("\n 导入原理...")
    db.import_principles_from_json(principle_file)
    
    print("\n 导入矛盾矩阵...")
    db.import_matrix_from_json(matrix_file)
    
    # 验证
    print("\n" + "="*50)
    print("验证结果")
    print("="*50)
    
    params = db.get_all_parameters()
    principles = db.get_all_principles()
    print(f"   参数表: {len(params)} 条")
    print(f"   原理表: {len(principles)} 条")
    
    # 显示前几条参数
    if params:
        print("\n 参数示例:")
        for p in params[:3]:
            print(f"   ID:{p['id']} - {p['name_cn']}")
    
    # 显示前几条原理
    if principles:
        print("\n原理示例:")
        for p in principles[:3]:
            print(f"   ID:{p['id']} - {p['name_cn']}")
    
    # 测试矩阵查询
    if matrix_file.exists():
        # 获取第一条矩阵记录测试
        with open(matrix_file, 'r', encoding='utf-8') as f:
            matrix_data = json.load(f)
            if matrix_data and isinstance(matrix_data, list) and len(matrix_data) > 0:
                first = matrix_data[0]
                improve_id = first.get('improve_id')
                worsen_id = first.get('worsen_id')
                if improve_id and worsen_id:
                    principles = db.get_principles_by_matrix(improve_id, worsen_id)
                    print(f"\n矛盾矩阵测试 ({improve_id}→{worsen_id}):")
                    print(f"   推荐原理: {principles}")
    
    print("\n数据导入完成！")

if __name__ == "__main__":
    import json
    main()