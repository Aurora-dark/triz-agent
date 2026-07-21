# api/services/matrix_service.py
import json
import re
from pathlib import Path
from typing import List, Dict, Optional

MATRIX_PATH = Path(__file__).parent.parent.parent / "data" / "triz_matrix.json"
PRINCIPLES_DETAIL_PATH = Path(__file__).parent.parent.parent / "data" / "principles_detail.json"


class MatrixService:
    def __init__(self):
        self._load_data()
        self._load_principles_detail()
        self._init_mappings()

    # ==================== 数据加载 ====================

    def _load_data(self):
        try:
            with open(MATRIX_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.parameters = data.get("参数列表", {})
                self.principles = data.get("发明原理", {})
                self.matrix = data.get("矩阵", {})
                print(f"✅ 加载矛盾矩阵成功: {len(self.matrix)} 条映射关系")
        except FileNotFoundError:
            print("⚠️ 矩阵数据文件未找到，使用空数据")
            self.parameters = {}
            self.principles = {}
            self.matrix = {}

    def _load_principles_detail(self):
        try:
            with open(PRINCIPLES_DETAIL_PATH, "r", encoding="utf-8") as f:
                self.principles_detail = json.load(f)
            print(f"✅ 加载原理详情成功: {len(self.principles_detail)} 条")
        except FileNotFoundError:
            print("⚠️ 原理详情文件未找到")
            self.principles_detail = {}

    # ==================== 映射表初始化 ====================

    def _init_mappings(self):
        # ---------- 参数映射（模型输出 → 标准参数名称）----------
        self.param_mapping = {
            # 速度/动力
            "31 动力性": "速度",
            "动力性": "速度",
            "动力": "速度",
            "加速性能": "速度",
            "加速": "速度",
            "速度": "速度",
            # 油耗/能耗
            "20 油耗": "能量消耗",
            "油耗": "能量消耗",
            "燃料消耗": "能量消耗",
            "耗油": "能量消耗",
            "能耗": "能量消耗",
            "能量消耗": "能量消耗",
            # 重量
            "07替代材料": "运动物体的重量",
            "替代材料": "运动物体的重量",
            "轻量化": "运动物体的重量",
            "减轻重量": "运动物体的重量",
            "更轻": "运动物体的重量",
            "重量减轻": "运动物体的重量",
            "重量": "运动物体的重量",
            "增加的重量或体积": "运动物体的重量",
            "增加的重量": "运动物体的重量",
            "运动物体的重量": "运动物体的重量",
            # 强度
            "12强度": "强度",
            "强度": "强度",
            "结构强度": "强度",
            "坚固": "强度",
            "硬度": "强度",
            # 屏幕面积
            "屏幕尺寸": "运动物体的面积",
            "屏幕": "运动物体的面积",
            "显示面积": "运动物体的面积",
            "运动物体的面积": "运动物体的面积",
            # 操作性
            "单手操作便利性": "可操作性",
            "操作性": "可操作性",
            "可操作性": "可操作性",
            "操作的便利性": "可操作性",
            # 精度/测量 (完整覆盖各种格式)
            "26 (精确度)": "测量精度",
            "26(精确度)": "测量精度",
            "26 精确度": "测量精度",
            "精确度": "测量精度",
            "精度": "测量精度",
            "测量精度": "测量精度",
            "减少误差": "测量精度",
            "10（精度）": "测量精度",
            "10(精度)": "测量精度",
            "10 精度": "测量精度",
            # 复杂性/维护
            "14 (操作复杂性/维护成本)": "系统复杂性",
            "14(操作复杂性/维护成本)": "系统复杂性",
            "14 操作复杂性": "系统复杂性",
            "操作复杂性": "系统复杂性",
            "系统复杂性": "系统复杂性",
            "维护成本": "可维护性",
            # 生产率 (完整覆盖各种格式)
            "生产效率": "生产率",
            "生产率": "生产率",
            "生产效率降低": "生产率",
            "15 (生产率)": "生产率",
            "24（生产率）": "生产率",
            "24(生产率)": "生产率",
            "24 生产率": "生产率",
            # 其他
            "电池续航": "能量消耗",
            "续航": "能量消耗",
            "电量": "能量消耗",
            "充电时间": "时间损失",
            "充电": "时间损失",
            "时间损失": "时间损失",
            "存储空间": "物质数量",
            "存储": "物质数量",
            "物质数量": "物质数量",
            "噪音": "作用于物体的有害因素",
            "噪声": "作用于物体的有害因素",
            "作用于物体的有害因素": "作用于物体的有害因素",
            "成本": "物质损失",
            "物质损失": "物质损失",
        }

        # ---------- 编号映射（模型输出的编号 → 标准参数ID）----------
        self.id_mapping = {
            "26": "28",    # 精确度 → 测量精度
            "14": "36",    # 操作复杂性 → 系统复杂性
            "31": "9",     # 动力性 → 速度
            "20": "20",    # 油耗 → 能量消耗
            "07": "1",     # 替代材料 → 运动物体的重量
            "12": "14",    # 强度 → 强度
            "45": "5",     # 屏幕尺寸 → 运动物体的面积
            "33": "33",    # 可操作性 → 可操作性
            "28": "28",    # 测量精度 → 测量精度
            "36": "36",    # 系统复杂性 → 系统复杂性
            "34": "34",    # 可维护性 → 可维护性
            "39": "39",    # 生产率 → 生产率
            "25": "25",    # 时间损失 → 时间损失
            "30": "30",    # 作用于物体的有害因素
            "23": "23",    # 物质损失 → 物质损失
            "071": "28",   # 减少误差 → 测量精度
            "062": "39",   # 生产效率降低 → 生产率
            "15": "39",    # 生产率
            "10": "28",    # 精度 → 测量精度  ← 🆕
            "24": "39",    # 生产率 → 生产率    ← 🆕
        }

        # ---------- 同义词映射 ----------
        self.synonyms = {
            "速度": "速度",
            "能量消耗": "能量消耗",
            "运动物体的重量": "运动物体的重量",
            "强度": "强度",
            "运动物体的面积": "运动物体的面积",
            "可操作性": "可操作性",
            "时间损失": "时间损失",
            "物质数量": "物质数量",
            "作用于物体的有害因素": "作用于物体的有害因素",
            "测量精度": "测量精度",
            "系统复杂性": "系统复杂性",
            "可维护性": "可维护性",
            "生产率": "生产率",
            "物质损失": "物质损失",
        }

    # ==================== 核心方法 ====================

    def get_param_name(self, param_id: str) -> str:
        return self.parameters.get(str(param_id), "")

    def get_param_id(self, param_name: str) -> Optional[str]:
        if not param_name:
            return None

        original = param_name.strip()
        param = original

        # 1. 直接匹配
        for pid, name in self.parameters.items():
            if param == name:
                return pid

        # 2. 参数映射
        if param in self.param_mapping:
            mapped = self.param_mapping[param]
            print(f"🔄 参数映射: '{original}' → '{mapped}'")
            param = mapped
            for pid, name in self.parameters.items():
                if param == name:
                    return pid

        # 3. 同义词映射
        if param in self.synonyms:
            mapped = self.synonyms[param]
            if mapped != param:
                print(f"🔄 同义词映射: '{original}' → '{mapped}'")
                param = mapped
                for pid, name in self.parameters.items():
                    if param == name:
                        return pid

        # 4. 智能清洗
        def clean(text: str) -> str:
            if not text:
                return text
            res = text.strip()
            # 去除括号内容
            res = re.sub(r'[（(][^）)]*[）)]', '', res).strip()
            # 去除 "数字 - " 前缀（支持多种连字符）
            res = re.sub(r'^\d+\s*[-—－－]\s*', '', res).strip()
            # 残留连字符
            res = re.sub(r'^[-—－－]\s*', '', res).strip()
            # 去除末尾标点
            res = re.sub(r'[。，、：；！？\s]+$', '', res).strip()
            return res

        cleaned = clean(param)
        if cleaned != param and cleaned:
            print(f"🔄 清洗: '{param}' → '{cleaned}'")
            param = cleaned
            # 清洗后再次尝试映射
            if param in self.param_mapping:
                mapped = self.param_mapping[param]
                print(f"🔄 参数映射(清洗后): '{cleaned}' → '{mapped}'")
                param = mapped
            if param in self.synonyms:
                mapped = self.synonyms[param]
                if mapped != param:
                    print(f"🔄 同义词映射(清洗后): '{cleaned}' → '{mapped}'")
                    param = mapped
            for pid, name in self.parameters.items():
                if param == name:
                    return pid

        # 5. 精确匹配（再次）
        for pid, name in self.parameters.items():
            if param == name:
                return pid

        # 6. 包含匹配
        for pid, name in self.parameters.items():
            if param in name or name in param:
                return pid

        # 7. 提取数字ID并映射
        match = re.search(r"(\d+)", original)
        if match:
            num = match.group(1)
            if num in self.id_mapping:
                mapped_id = self.id_mapping[num]
                print(f"🔄 编号映射: '{original}' → ID '{mapped_id}'")
                return mapped_id
            if num in self.parameters:
                print(f"🔄 提取ID: '{original}' → ID '{num}'")
                return num

        print(f"⚠️ 未找到匹配参数: '{original}'")
        return None

    def get_principle_detail(self, principle_name: str) -> Dict:
        return self.principles_detail.get(principle_name, {})

    def get_principles_by_ids(self, principle_ids: List[int]) -> List[str]:
        return [self.principles.get(str(p), f"原理{p}") for p in principle_ids]

    def get_recommendation(self, improve: str, worsen: str) -> Dict:
        improve_id = self.get_param_id(improve)
        worsen_id = self.get_param_id(worsen)

        if not improve_id or not worsen_id:
            return {
                "改善参数": improve,
                "恶化参数": worsen,
                "改善参数ID": improve_id,
                "恶化参数ID": worsen_id,
                "推荐原理ID": [],
                "推荐原理名称": [],
                "是否有匹配": False,
            }

        improve_name = self.get_param_name(improve_id)
        worsen_name = self.get_param_name(worsen_id)

        key = f"{improve_name}_{worsen_name}"
        if key in self.matrix:
            principle_ids = self.matrix[key]
            return {
                "改善参数": improve_name,
                "恶化参数": worsen_name,
                "改善参数ID": improve_id,
                "恶化参数ID": worsen_id,
                "推荐原理ID": principle_ids,
                "推荐原理名称": self.get_principles_by_ids(principle_ids),
                "是否有匹配": True,
            }

        reverse_key = f"{worsen_name}_{improve_name}"
        if reverse_key in self.matrix:
            principle_ids = self.matrix[reverse_key]
            return {
                "改善参数": improve_name,
                "恶化参数": worsen_name,
                "改善参数ID": improve_id,
                "恶化参数ID": worsen_id,
                "推荐原理ID": principle_ids,
                "推荐原理名称": self.get_principles_by_ids(principle_ids),
                "是否有匹配": True,
            }

        return {
            "改善参数": improve_name,
            "恶化参数": worsen_name,
            "改善参数ID": improve_id,
            "恶化参数ID": worsen_id,
            "推荐原理ID": [],
            "推荐原理名称": [],
            "是否有匹配": False,
        }

    def get_all_parameters(self) -> Dict[str, str]:
        return self.parameters

    def get_all_principles(self) -> Dict[str, str]:
        return self.principles


matrix_service = MatrixService()