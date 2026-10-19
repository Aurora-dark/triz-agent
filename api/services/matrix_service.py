# api/services/matrix_service.py
"""
矛盾矩阵服务：参数标准化 + 矩阵查询 + 原理详情。

数据来自 data/triz_matrix.json 与 data/principles_detail.json，
后者由 scripts/build_principles_detail.py 从 40 条原理原始数据生成。
"""

import json
import re
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, List, Optional

MATRIX_PATH = Path(__file__).parent.parent.parent / "data" / "triz_matrix.json"
PRINCIPLES_DETAIL_PATH = (
    Path(__file__).parent.parent.parent / "data" / "principles_detail.json"
)

# 通用别名（模型常见输出 -> 39 个标准参数名）。
# 只做跨场景的参数同义归一，不绑定任何具体产品场景。
PARAM_ALIASES = {
    "动力": "速度",
    "动力性": "速度",
    "加速": "速度",
    "加速性能": "速度",
    "油耗": "运动物体的能耗",
    "燃料消耗": "运动物体的能耗",
    "耗油": "运动物体的能耗",
    "能耗": "运动物体的能耗",
    "能量消耗": "运动物体的能耗",
    "电池续航": "运动物体的能耗",
    "续航": "运动物体的能耗",
    "电量": "运动物体的能耗",
    "重量": "运动物体的重量",
    "质量": "运动物体的重量",
    "轻量化": "运动物体的重量",
    "减轻重量": "运动物体的重量",
    "更轻": "运动物体的重量",
    "强度": "强度",
    "结构强度": "强度",
    "坚固": "强度",
    "硬度": "强度",
    "面积": "运动物体的面积",
    "屏幕尺寸": "运动物体的面积",
    "显示面积": "运动物体的面积",
    "操作性": "可操作性",
    "操作便利性": "可操作性",
    "单手操作便利性": "可操作性",
    "操作的便利性": "可操作性",
    "精度": "测量精度",
    "精确度": "测量精度",
    "减少误差": "测量精度",
    "误差": "测量精度",
    "复杂性": "系统的复杂性",
    "系统复杂性": "系统的复杂性",
    "操作复杂性": "系统的复杂性",
    "维护成本": "可维护性",
    "生产效率": "生产率",
    "生产效率降低": "生产率",
    "效率": "生产率",
    "充电时间": "时间损失",
    "时间": "时间损失",
    "存储空间": "物质数量",
    "存储": "物质数量",
    "噪音": "作用于物体的有害因素",
    "噪声": "作用于物体的有害因素",
    "成本": "物质损失",
    "可靠性": "可靠性",
    "耐用性": "运动物体的耐久性",
    "寿命": "运动物体的耐久性",
    "温度": "温度",
    "热量": "温度",
    "光照": "光照度",
    "亮度": "光照度",
    "体积": "运动物体的体积",
}

# 数字前缀里常见的「模型自定义编号 -> 标准 ID」历史映射。
# 仅用于旧 prompt 输出中「编号与名称不匹配」的情况；正常情况下优先按名称匹配。
LEGACY_ID_HINTS = {
    "10": "28",  # 10（精度）
    "14": "36",  # 14（操作复杂性）
    "15": "39",  # 15（生产率）
    "20": "19",  # 20（油耗/能量消耗）→ 运动物体的能耗
    "24": "39",  # 24（生产率）
    "26": "28",  # 26（精确度）
    "31": "9",   # 31（动力性）
    "45": "5",   # 45（屏幕尺寸）
}

_BRACKET_RE = re.compile(r"[（(][^）)]*[）)]")


class MatrixService:
    def __init__(self):
        self.parameters: Dict[str, str] = {}
        self.principles: Dict[str, str] = {}
        self.matrix: Dict[str, List[int]] = {}
        self.principles_detail: Dict[str, Dict] = {}
        self._load_data()
        self._load_principles_detail()
        self._name_to_id = {name: pid for pid, name in self.parameters.items()}

    # ==================== 数据加载 ====================

    def _load_data(self):
        try:
            data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
            self.parameters = data.get("参数列表", {})
            self.principles = data.get("发明原理", {})
            self.matrix = data.get("矩阵", {})
            print(f"✅ 加载矛盾矩阵成功: {len(self.matrix)} 条映射关系")
        except FileNotFoundError:
            print(f"⚠️ 矩阵数据文件未找到: {MATRIX_PATH}")

    def _load_principles_detail(self):
        try:
            self.principles_detail = json.loads(
                PRINCIPLES_DETAIL_PATH.read_text(encoding="utf-8")
            )
            print(f"✅ 加载原理详情成功: {len(self.principles_detail)} 条")
        except FileNotFoundError:
            print(f"⚠️ 原理详情文件未找到: {PRINCIPLES_DETAIL_PATH}")
            self.principles_detail = {}

    # ==================== 参数标准化 ====================

    @staticmethod
    def _clean(text: str) -> str:
        text = text.strip()
        text = text.replace("（", "(").replace("）", ")")
        text = _BRACKET_RE.sub("", text)
        text = text.strip(" \t\r\n。．，、：；!！?？-—－_")
        return text

    def _exact(self, name: str) -> Optional[str]:
        if name in self._name_to_id:
            return self._name_to_id[name]
        return None

    def _alias(self, name: str) -> Optional[str]:
        target = PARAM_ALIASES.get(name)
        if target:
            pid = self._exact(target)
            if pid:
                return pid
        return None

    def get_param_id(self, param_name: str) -> Optional[str]:
        """标准名 → 别名 → 数字前缀 → 子串/模糊匹配。"""
        if not param_name:
            return None

        original = param_name.strip()
        name = self._clean(original)

        # 1. 标准名精确匹配
        pid = self._exact(name)
        if pid:
            return pid

        # 2. 别名
        pid = self._alias(name)
        if pid:
            print(f"🔄 别名: '{original}' → ID {pid}")
            return pid

        # 3. 数字前缀：先去掉前缀按名称匹配，再按编号兜底
        match = re.match(r"^\s*(?:参数|序号)?\s*(\d{1,2})(.*)$", name)
        if match:
            number, tail = match.group(1), match.group(2)
            rest = tail.lstrip(" .、,，:：-—－\t").strip()
            if rest:
                pid = self._exact(rest) or self._alias(self._clean(rest))
                if pid:
                    print(f"🔄 去编号: '{original}' → ID {pid}")
                    return pid
            # 只有「纯编号」或「编号 + 分隔符」才把数字当作参数 ID，
            # 避免把 "2025年" 之类的文本误判成 20 号参数
            is_pure_number = not tail.strip()
            has_separator = bool(tail) and tail[0] in " .、,，:：-—－\t"
            if is_pure_number or has_separator:
                if number in self.parameters:
                    print(f"🔄 编号匹配: '{original}' → ID {number}")
                    return number
                if number in LEGACY_ID_HINTS:
                    print(f"🔄 历史编号: '{original}' → ID {LEGACY_ID_HINTS[number]}")
                    return LEGACY_ID_HINTS[number]

        # 4. 子串匹配（取最长命中）
        hits = [
            (len(name), pid)
            for pid, candidate in self.parameters.items()
            if len(name) >= 2 and (name in candidate or candidate in name)
        ]
        if hits:
            hits.sort(reverse=True)
            print(f"🔄 包含匹配: '{original}' → ID {hits[0][1]}")
            return hits[0][1]

        # 5. difflib 模糊匹配
        candidates = list(self.parameters.values())
        close = get_close_matches(name, candidates, n=1, cutoff=0.6)
        if close:
            pid = self._name_to_id[close[0]]
            print(f"🔄 模糊匹配: '{original}' → '{close[0]}' (ID {pid})")
            return pid

        print(f"⚠️ 未找到匹配参数: '{original}'")
        return None

    def get_param_name(self, param_id: str) -> str:
        return self.parameters.get(str(param_id), "")

    # ==================== 矩阵与原理 ====================

    def get_principle_detail(self, principle_name: str) -> Dict:
        return self.principles_detail.get(principle_name, {})

    def get_principles_by_ids(self, principle_ids: List[int]) -> List[str]:
        return [self.principles.get(str(pid), f"原理{pid}") for pid in principle_ids]

    def get_principle_items(self, principle_ids: List[int]) -> List[Dict]:
        """把原理 ID 展开成前端可直接渲染的名称 + 解释 + 案例。"""
        items = []
        for pid in principle_ids:
            name = self.principles.get(str(pid), f"原理{pid}")
            detail = self.get_principle_detail(name)
            items.append(
                {
                    "id": int(pid),
                    "name": name,
                    "explain": detail.get("explain", ""),
                    "case": detail.get("case", ""),
                }
            )
        return items

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
                "推荐原理详情": [],
                "是否有匹配": False,
            }

        improve_name = self.get_param_name(improve_id)
        worsen_name = self.get_param_name(worsen_id)

        principle_ids: List[int] = []
        matched = False
        for key in (f"{improve_name}_{worsen_name}", f"{worsen_name}_{improve_name}"):
            if key in self.matrix:
                principle_ids = self.matrix[key]
                matched = True
                break

        return {
            "改善参数": improve_name,
            "恶化参数": worsen_name,
            "改善参数ID": improve_id,
            "恶化参数ID": worsen_id,
            "推荐原理ID": principle_ids,
            "推荐原理名称": self.get_principles_by_ids(principle_ids),
            "推荐原理详情": self.get_principle_items(principle_ids),
            "是否有匹配": matched,
        }

    def get_all_parameters(self) -> Dict[str, str]:
        return self.parameters

    def get_all_principles(self) -> Dict[str, str]:
        return self.principles


matrix_service = MatrixService()
