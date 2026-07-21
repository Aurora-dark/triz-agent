# api/services/history_service.py
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# 数据库路径
DB_PATH = Path(__file__).parent.parent.parent / "storage" / "history.db"

class HistoryService:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE,
                    requirement TEXT,
                    improve_param TEXT,
                    worsen_param TEXT,
                    contradiction TEXT,
                    need_more_info INTEGER,
                    model_used TEXT,
                    processing_time_ms INTEGER,
                    created_at TEXT
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_requirement 
                ON history(requirement)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON history(created_at DESC)
            ''')
    
    def save(self, task_id: str, result: dict, processing_time_ms: int = 0, model_used: str = None):
        """保存分析结果"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO history 
                (task_id, requirement, improve_param, worsen_param, contradiction, 
                 need_more_info, model_used, processing_time_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                result.get('原始需求', ''),
                result.get('改善参数', ''),
                result.get('恶化参数', ''),
                result.get('矛盾描述', ''),
                1 if result.get('是否需要补充信息', False) else 0,
                model_used,
                processing_time_ms,
                datetime.now().isoformat()
            ))
    
    def get_all(self, limit: int = 50) -> List[Dict]:
        """获取历史记录列表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM history 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_task_id(self, task_id: str) -> Optional[Dict]:
        """根据任务ID获取单条记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM history WHERE task_id = ?', 
                (task_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def search(self, keyword: str) -> List[Dict]:
        """搜索历史记录（按需求文本）"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM history 
                WHERE requirement LIKE ? 
                ORDER BY created_at DESC
            ''', (f'%{keyword}%',))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete(self, task_id: str):
        """删除单条记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM history WHERE task_id = ?', (task_id,))
    
    def count(self) -> int:
        """获取记录总数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM history')
            return cursor.fetchone()[0]

# 全局单例
history_service = HistoryService()