# api/services/task_manager.py
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from ..config import TASKS_DIR

class TaskManager:
    """任务状态管理器（基于文件存储，生产环境可替换为Redis）"""
    
    def __init__(self):
        self.tasks_dir = TASKS_DIR
    
    def _get_task_path(self, task_id: str) -> Path:
        return self.tasks_dir / f"{task_id}.json"
    
    def create_task(self, requirement_text: str, user_id: str = None, session_id: str = None, metadata: dict = None) -> str:
        """创建新任务"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        task_data = {
            "task_id": task_id,
            "requirement_text": requirement_text,
            "user_id": user_id,
            "session_id": session_id,
            "metadata": metadata or {},
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "result": None,
            "processing_time_ms": None,
            "model_used": None,
            "error": None
        }
        
        self._save_task(task_id, task_data)
        return task_id
    
    def _save_task(self, task_id: str, task_data: dict):
        """保存任务数据"""
        with open(self._get_task_path(task_id), 'w', encoding='utf-8') as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务数据"""
        task_path = self._get_task_path(task_id)
        if not task_path.exists():
            return None
        
        with open(task_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_task(self, task_id: str, **kwargs):
        """更新任务数据"""
        task_data = self.get_task(task_id)
        if task_data:
            task_data.update(kwargs)
            self._save_task(task_id, task_data)
    
    def set_result(self, task_id: str, result: dict, processing_time_ms: int, model_used: str):
        """设置提取结果"""
        self.update_task(
            task_id,
            status="completed",
            result=result,
            processing_time_ms=processing_time_ms,
            model_used=model_used,
            completed_at=datetime.now().isoformat()
        )
    
    def set_error(self, task_id: str, error: str):
        """设置错误状态"""
        self.update_task(
            task_id,
            status="failed",
            error=error,
            completed_at=datetime.now().isoformat()
        )
    
    def task_exists(self, task_id: str) -> bool:
        """检查任务是否存在"""
        return self._get_task_path(task_id).exists()

# 全局单例
task_manager = TaskManager()