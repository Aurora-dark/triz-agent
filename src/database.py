"""
关系型数据库模块 - 支持分开的JSON文件导入
"""

import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from typing import List, Dict, Optional

class TRIZDatabase:
    """TRIZ数据库管理器"""
    
    def __init__(self, db_path="data/processed/triz.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_tables(self):
        """创建数据表"""
        with self.get_connection() as conn:
            # 1. 参数表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS triz_parameters (
                    id INTEGER PRIMARY KEY,
                    name_cn TEXT,
                    name_en TEXT,
                    desc_cn TEXT,
                    desc_en TEXT,
                    opposite_id INTEGER,
                    tag_cn TEXT,
                    tag_en TEXT
                )
            ''')
            
            # 2. 原理表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS triz_principles (
                    id INTEGER PRIMARY KEY,
                    name_cn TEXT,
                    name_en TEXT,
                    explain_cn TEXT,
                    explain_en TEXT,
                    case_cn TEXT,
                    case_en TEXT,
                    tag_cn TEXT,
                    tag_en TEXT
                )
            ''')
            
            # 3. 矛盾矩阵表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS triz_matrix (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    improve_id INTEGER,
                    worsen_id INTEGER,
                    principle_ids TEXT,
                    UNIQUE(improve_id, worsen_id)
                )
            ''')
            
            conn.commit()
    
    def import_parameters_from_json(self, json_path: Path):
        """从JSON文件导入参数"""
        with open(json_path, 'r', encoding='utf-8') as f:
            params = json.load(f)
        
        # 如果是单个对象，转换为列表
        if isinstance(params, dict):
            params = [params]
        
        with self.get_connection() as conn:
            conn.execute("DELETE FROM triz_parameters")
            for p in params:
                conn.execute('''
                    INSERT OR REPLACE INTO triz_parameters 
                    (id, name_cn, name_en, desc_cn, desc_en, opposite_id, tag_cn, tag_en)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    p.get('id'),
                    p.get('name_cn', ''),
                    p.get('name_en', ''),
                    p.get('desc_cn', p.get('explain_cn', '')),
                    p.get('desc_en', p.get('explain_en', '')),
                    p.get('opposite_id'),
                    p.get('tag_cn', ''),
                    p.get('tag_en', '')
                ))
            conn.commit()
        
        print(f" 导入 {len(params)} 个工程参数")
    
    def import_principles_from_json(self, json_path: Path):
        """从JSON文件导入原理"""
        with open(json_path, 'r', encoding='utf-8') as f:
            principles = json.load(f)
        
        if isinstance(principles, dict):
            principles = [principles]
        
        with self.get_connection() as conn:
            conn.execute("DELETE FROM triz_principles")
            for p in principles:
                conn.execute('''
                    INSERT OR REPLACE INTO triz_principles 
                    (id, name_cn, name_en, explain_cn, explain_en, case_cn, case_en, tag_cn, tag_en)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    p.get('id'),
                    p.get('name_cn', ''),
                    p.get('name_en', ''),
                    p.get('explain_cn', ''),
                    p.get('explain_en', ''),
                    p.get('case_cn', ''),
                    p.get('case_en', ''),
                    p.get('tag_cn', ''),
                    p.get('tag_en', '')
                ))
            conn.commit()
        
        print(f" 导入 {len(principles)} 个发明原理")
    
    def import_matrix_from_json(self, json_path: Path):
        """从JSON文件导入矛盾矩阵"""
        with open(json_path, 'r', encoding='utf-8') as f:
            matrix = json.load(f)
        
        if isinstance(matrix, dict):
            matrix = [matrix]
        
        with self.get_connection() as conn:
            conn.execute("DELETE FROM triz_matrix")
            for m in matrix:
                principle_ids = m.get('principle_ids', [])
                conn.execute('''
                    INSERT OR REPLACE INTO triz_matrix 
                    (improve_id, worsen_id, principle_ids)
                    VALUES (?, ?, ?)
                ''', (
                    m.get('improve_id'),
                    m.get('worsen_id'),
                    json.dumps(principle_ids)
                ))
            conn.commit()
        
        print(f" 导入 {len(matrix)} 条矛盾矩阵记录")
    
    def get_principles_by_matrix(self, improve_id: int, worsen_id: int) -> List[int]:
        """根据矛盾查询推荐原理"""
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT principle_ids FROM triz_matrix WHERE improve_id=? AND worsen_id=?",
                (improve_id, worsen_id)
            ).fetchone()
            if result:
                return json.loads(result['principle_ids'])
            
            # 尝试交换
            result = conn.execute(
                "SELECT principle_ids FROM triz_matrix WHERE improve_id=? AND worsen_id=?",
                (worsen_id, improve_id)
            ).fetchone()
            if result:
                return json.loads(result['principle_ids'])
            
            return []
    
    def get_parameter_by_id(self, pid: int) -> Optional[dict]:
       with self.get_connection() as conn:
        result = conn.execute(
            "SELECT * FROM triz_parameters WHERE id=?", (pid,)
        ).fetchone()
        if result:
            data = dict(result)
            if 'name_cn' in data and 'name' not in data:
                data['name'] = data['name_cn']
            return data
        return None
    def get_principle_by_id(self, pid: int) -> Optional[dict]:
     with self.get_connection() as conn:
        result = conn.execute(
            "SELECT * FROM triz_principles WHERE id=?", (pid,)
        ).fetchone()
        if result:
            data = dict(result)
            # 添加 name 字段作为 name_cn 的别名
            if 'name_cn' in data and 'name' not in data:
                data['name'] = data['name_cn']
            return data
        return None
    
    def get_all_parameters(self) -> List[dict]:
        with self.get_connection() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM triz_parameters ORDER BY id")]
    
    def get_all_principles(self) -> List[dict]:
        with self.get_connection() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM triz_principles ORDER BY id")]