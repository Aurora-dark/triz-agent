"""
TRIZ解题引擎 - 整合数据库和向量库
"""

from src.database import TRIZDatabase
from src.vector_store import VectorStore

class TRIZSolver:
    """TRIZ问题求解器"""
    
    def __init__(self):
        self.db = TRIZDatabase()
        self.vector_store = VectorStore()
        
        # 加载向量索引
        try:
            self.vector_store.load()
        except FileNotFoundError:
            print("向量索引不存在，请先运行 build_vector_index.py")
    
    def solve(self, problem_description: str, top_k: int = 3) -> dict:
        """
        解决技术问题
        """
        print(f"\n问题: {problem_description}")
        
        # 1. 语义检索找到相关参数
        matched_params = self.vector_store.search(problem_description, top_k=3)
        
        if not matched_params:
            return {'error': '未找到相关参数', 'problem': problem_description}
        
        print(f"\n识别到的TRIZ参数:")
        for p in matched_params:
            print(f"   • {p['name']} (相似度: {p['similarity']:.3f})")
        
        # 2. 取最相关的作为改善参数，第二个作为恶化参数
        improving = matched_params[0]
        worsening = matched_params[1] if len(matched_params) > 1 else matched_params[0]
        
        # 3. 查询矛盾矩阵
        principle_ids = self.db.get_principles_by_matrix(improving['id'], worsening['id'])
        
        if not principle_ids:
            # 如果没有直接解，尝试交换
            principle_ids = self.db.get_principles_by_matrix(worsening['id'], improving['id'])
        
        # 4. 获取原理详情
        principles = []
        for pid in principle_ids:
            p = self.db.get_principle_by_id(pid)
            if p:
                principles.append(dict(p))
        
        # 5. 返回结果
        result = {
            'problem': problem_description,
            'improving_parameter': improving,
            'worsening_parameter': worsening,
            'principles': principles,
            'confidence': improving['similarity']
        }
        
        print(f"\n推荐发明原理:")
        for i, p in enumerate(principles, 1):
            print(f"   {i}. {p['name']} - {p.get('description', '')[:50]}...")
        
        return result
    
    def interactive(self):
        """交互式命令行界面"""
        print("\n" + "="*50)
        print(" TRIZ智能解题助手")
        print("="*50)
        print("输入你的技术问题，我会推荐TRIZ解决方案")
        print("输入 'quit' 退出\n")
        
        while True:
            problem = input("\n💬 你的问题: ").strip()
            if problem.lower() in ['quit', 'exit', 'q']:
                print("再见！")
                break
            if not problem:
                continue
            
            try:
                self.solve(problem)
            except Exception as e:
                print(f"错误: {e}")