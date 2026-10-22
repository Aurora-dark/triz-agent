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
    # ---- 工程场景通用词 ----
    "主频": "速度",
    "频率": "速度",
    "转速": "速度",
    "速率": "速度",
    "切削速度": "速度",
    "注塑速度": "速度",
    "传输速率": "速度",
    "刷新率": "速度",
    "节拍": "速度",
    "跨度": "运动物体的长度",
    "跨径": "运动物体的长度",
    "高度": "运动物体的长度",
    "厚度": "运动物体的长度",
    "长度": "运动物体的长度",
    "距离": "运动物体的长度",
    "行程": "运动物体的长度",
    "推力": "力",
    "扭矩": "力",
    "扭矩密度": "力",
    "转矩": "力",
    "载荷": "力",
    "承载": "力",
    "承载力": "力",
    "承载能力": "力",
    "功率": "功率",
    "电流": "功率",
    "输出功率": "功率",
    "充电功率": "功率",
    "发热": "温度",
    "油温": "温度",
    "温升": "温度",
    "散热": "温度",
    "热影响区": "温度",
    "过热": "温度",
    "功耗": "运动物体的能耗",
    "耗电": "运动物体的能耗",
    "电耗": "运动物体的能耗",
    "光洁度": "制造精度",
    "一致性": "制造精度",
    "表面质量": "制造精度",
    "加工质量": "制造精度",
    "制造精度": "制造精度",
    "抗震": "结构的稳定性",
    "抗震等级": "结构的稳定性",
    "稳定性": "结构的稳定性",
    "稳固": "结构的稳定性",
    "刚度": "强度",
    "刚度不足": "强度",
    "刚性": "强度",
    "磨损": "运动物体的耐久性",
    "耐腐蚀": "运动物体的耐久性",
    "耐用": "运动物体的耐久性",
    "防水": "可靠性",
    "可靠": "可靠性",
    "物料洒落": "物质损失",
    "洒落": "物质损失",
    "破损": "物质损失",
    "浪费": "物质损失",
    "材料用量": "物质损失",
    "钢材用量": "物质损失",
    "用量": "物质损失",
    "造价": "物质损失",
    "损耗": "物质损失",
    "耗时": "时间损失",
    "工期": "时间损失",
    "周期": "时间损失",
    "等待时间": "时间损失",
    "抛光时间": "时间损失",
    "固化时间": "时间损失",
    "调试时间": "时间损失",
    "装配时间": "时间损失",
    "翘曲": "形状",
    "变形": "形状",
    "采光面积": "运动物体的面积",
    "采光": "运动物体的面积",
    "电池容量": "物质数量",
    "容量": "物质数量",
    "控制复杂度": "控制的复杂性",
    "控制复杂性": "控制的复杂性",
    "控制系统复杂性": "控制的复杂性",
    "控制系统复杂度": "控制的复杂性",
    "控制系统": "控制的复杂性",
    "调试困难": "控制的复杂性",
    "调试": "控制的复杂性",
    "控制难度": "控制的复杂性",
    "复杂度": "系统的复杂性",
    "自动化程度": "自动化程度",
    "自动化": "自动化程度",
    "产能": "生产率",
    "产量": "生产率",
    "信号": "信息损失",
    "信息": "信息损失",
    "数据丢失": "信息损失",
    "自重": "运动物体的重量",
    "机身重量": "运动物体的重量",
    "整机重量": "运动物体的重量",
    "结构重量": "运动物体的重量",
    "照度": "光照度",
    "光照度": "光照度",
    "截面尺寸": "运动物体的体积",
    "截面": "运动物体的体积",
    "腔体": "运动物体的体积",
    "容积": "运动物体的体积",
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
_LEADING_VERBS_RE = re.compile(
    r"^(?:提高|增加|增大|加强|提升|减少|降低|减小|缩短|减轻|加快|延长|扩大|缩小|优化|改善|加速|变长|变短|变大|变小)+"
)
_TRAILING_STATES_RE = re.compile(
    r"(?:变长|变短|变大|变小|增加|下降|上升|加剧|不足|困难|严重|明显|变差|降低|提高)+$"
)

# 参数语义簇：精确组合查不到时，用同簇参数做近似推荐
PARAM_CLUSTERS = [
    [1, 2, 3, 4, 5, 6, 7, 8],          # 重量/尺寸/面积/体积
    [9, 10, 19, 20, 21, 22],           # 速度/力/能耗/功率/能量损失
    [11, 13, 14, 15, 16],              # 应力/稳定性/强度/耐久性
    [12, 17, 18],                      # 形状/温度/光照
    [23, 24, 25, 26],                  # 物质/信息/时间损失/物质数量
    [27, 28, 29],                      # 可靠性/测量精度/制造精度
    [30, 31, 32, 33, 34, 35],          # 有害因素/可制造/操作/维护/适应性
    [36, 37, 38, 39],                  # 系统复杂性/控制复杂性/自动化/生产率
]


class MatrixService:
    def __init__(self):
        self.parameters: Dict[str, str] = {}
        self.principles: Dict[str, str] = {}
        self.matrix: Dict[str, List[int]] = {}
        self.principles_detail: Dict[str, Dict] = {}
        self._load_data()
        self._load_principles_detail()
        self._name_to_id = {name: pid for pid, name in self.parameters.items()}
        self._neighbors = self._build_neighbors()

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
        text = _LEADING_VERBS_RE.sub("", text)
        text = _TRAILING_STATES_RE.sub("", text)
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
        # 包含式别名：取最长的命中词，避免「控制复杂度」被「复杂度」抢走
        matches = [
            (len(key), value)
            for key, value in PARAM_ALIASES.items()
            if len(key) >= 2 and key in name
        ]
        if matches:
            _, target = max(matches)
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

    def _build_neighbors(self) -> Dict[str, set]:
        neighbors = {name: set() for name in self.parameters.values()}
        for cluster in PARAM_CLUSTERS:
            names = [self.parameters.get(str(pid), "") for pid in cluster]
            names = [name for name in names if name]
            for name in names:
                neighbors[name].update(n for n in names if n != name)
        return neighbors

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

    def _suggestions(self, improve_name: str, worsen_name: str) -> Dict[str, List[Dict]]:
        """精确和近似都查不到时，给出可点击的相邻参数建议。"""

        def side_candidates(name: str, index: int) -> List[Dict]:
            counts: Dict[str, int] = {}
            for key in self.matrix:
                candidate = key.split("_")[index]
                if candidate in self._neighbors.get(name, set()):
                    counts[candidate] = counts.get(candidate, 0) + 1
            return [
                {"name": candidate, "id": self._name_to_id[candidate], "组合数": count}
                for candidate, count in sorted(
                    counts.items(), key=lambda item: (-item[1], item[0])
                )[:3]
            ]

        return {
            "改善参数建议": side_candidates(improve_name, 0),
            "恶化参数建议": side_candidates(worsen_name, 1),
        }

    def _approximate(self, improve_name: str, worsen_name: str):
        """用同簇参数做近似匹配，返回 (命中组合, 聚合后的原理 ID)。"""
        improve_neighbors = self._neighbors.get(improve_name, set())
        worsen_neighbors = self._neighbors.get(worsen_name, set())

        scored = []
        for key, ids in self.matrix.items():
            improve_candidate, worsen_candidate = key.split("_")
            if improve_candidate == improve_name and worsen_candidate == worsen_name:
                continue
            if improve_candidate in improve_neighbors and worsen_candidate == worsen_name:
                score = 3
            elif improve_candidate == improve_name and worsen_candidate in worsen_neighbors:
                score = 3
            elif improve_candidate in improve_neighbors and worsen_candidate in worsen_neighbors:
                score = 2
            else:
                continue
            scored.append((score, key, ids))

        if not scored:
            return [], []

        scored.sort(key=lambda item: (-item[0], item[1]))
        top = scored[:3]
        weights: Dict[int, int] = {}
        for score, _, ids in top:
            for rank, pid in enumerate(ids):
                weights[pid] = weights.get(pid, 0) + score * (len(ids) - rank)
        ordered = [
            pid
            for pid, _ in sorted(weights.items(), key=lambda item: (-item[1], item[0]))
        ][:5]
        return [{"组合": key, "原理ID": ids} for _, key, ids in top], ordered

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
                "匹配类型": "未命中",
                "近似组合": [],
                "替代建议": {},
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

        if matched:
            return {
                "改善参数": improve_name,
                "恶化参数": worsen_name,
                "改善参数ID": improve_id,
                "恶化参数ID": worsen_id,
                "推荐原理ID": principle_ids,
                "推荐原理名称": self.get_principles_by_ids(principle_ids),
                "推荐原理详情": self.get_principle_items(principle_ids),
                "是否有匹配": True,
                "匹配类型": "精确",
                "近似组合": [],
                "替代建议": {},
            }

        near_combos, near_ids = self._approximate(improve_name, worsen_name)
        if near_ids:
            return {
                "改善参数": improve_name,
                "恶化参数": worsen_name,
                "改善参数ID": improve_id,
                "恶化参数ID": worsen_id,
                "推荐原理ID": near_ids,
                "推荐原理名称": self.get_principles_by_ids(near_ids),
                "推荐原理详情": self.get_principle_items(near_ids),
                "是否有匹配": True,
                "匹配类型": "近似",
                "近似组合": near_combos,
                "替代建议": self._suggestions(improve_name, worsen_name),
            }

        return {
            "改善参数": improve_name,
            "恶化参数": worsen_name,
            "改善参数ID": improve_id,
            "恶化参数ID": worsen_id,
            "推荐原理ID": [],
            "推荐原理名称": [],
            "推荐原理详情": [],
            "是否有匹配": False,
            "匹配类型": "未命中",
            "近似组合": [],
            "替代建议": self._suggestions(improve_name, worsen_name),
        }

    def get_all_parameters(self) -> Dict[str, str]:
        return self.parameters

    def get_all_principles(self) -> Dict[str, str]:
        return self.principles


matrix_service = MatrixService()
