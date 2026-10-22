# 🧠 TRIZ 智能体 · 本地化 AI 创新助手

基于 **TRIZ 方法论 + 本地大模型** 的技术矛盾自动提取与解决方案推荐系统。

## ✨ 功能特性

- 🔍 **矛盾提取**：输入技术需求，自动提取改善/恶化参数
- 🧠 **两阶段提取**：先抽「改善方面 / 恶化方面」，再映射到 39 个标准参数，降低小模型直接 39 选 1 的错误率
- 📐 **矛盾矩阵**：1190 条权威 TRIZ 映射关系（覆盖率 80.3%），自动推荐发明原理
- 💡 **原理详情**：每条推荐都带解释与工程案例
- 🧩 **近似兜底**：精确组合缺失时，按参数语义簇给出近似推荐与相邻参数建议
- 📋 **历史记录**：自动保存所有分析记录，支持搜索
- 🌐 **Web 界面**：开箱即用的可视化操作界面

## 🏗️ 技术架构

| 组件 | 技术 |
|------|------|
| 前端 | HTML + CSS + JavaScript |
| 后端 | FastAPI (Python) |
| 大模型 | Ollama + Qwen2.5:3B |
| 知识库 | TRIZ 矛盾矩阵 (JSON，1190 格) |
| 数据库 | SQLite |

## 📦 快速开始

1. 克隆项目

```bash
git clone https://github.com/Aurora-dark/triz-agent.git
cd triz-agent
```

2. 创建虚拟环境并安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

3. 安装 Ollama 并下载模型

```bash
ollama pull qwen2.5:3b
```

4. 一键启动（Windows）

```bat
start.bat
```

脚本会自动设置 `OLLAMA_MODELS`、按需拉起 Ollama、检查模型，然后启动 Web 服务并打开浏览器。

也可以手动启动：

```bash
.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

5. 访问 <http://127.0.0.1:8000>

## 📁 项目结构

```text
triz-agent/
├── api/                  # FastAPI 路由、服务、数据模型
│   ├── services/
│   │   ├── llm_client.py      # 两阶段矛盾提取
│   │   └── matrix_service.py  # 参数标准化 + 矩阵查询 + 近似兜底
│   └── main.py
├── data/
│   ├── triz_matrix.json       # 1190 格矛盾矩阵
│   ├── principles_detail.json # 40 条原理的解释与案例
│   ├── raw/                   # 原始数据与权威矩阵参考
│   ├── legacy/                # 旧矩阵备份与 A/B 报告
│   └── eval/                  # 30 条评测集 + 10 条留出集
├── scripts/              # 数据构建、评测脚本
├── static/index.html     # 前端界面
├── tests/                # pytest 回归测试
├── start.bat             # 一键启动
└── requirements.txt
```

## 🧪 测试与评测

```bash
# 回归测试（22 个用例）
python -m pytest

# 矩阵完整性 / 覆盖率校验
python scripts/rebuild_matrix.py --check

# 30 条主评测集
python scripts/evaluate_extraction.py

# 10 条留出集（估计泛化）
python scripts/evaluate_extraction.py --file data/eval/holdout.json --output data/eval/last_holdout.json
```

评测约定与结果解读见 [data/eval/README.md](data/eval/README.md)。

## 📝 使用示例

输入：电池续航短但机身要轻薄

```text
改善参数：19. 运动物体的能耗
恶化参数：1. 运动物体的重量
推荐原理：
  12. 等势        —— 消除高度差减少做功 / 码头登船桥
  18. 机械振动    —— 利用振动提升效率 / 振动筛分选物料
  28. 机械系统替代 —— 非机械方案替换机械结构 / 电磁门锁替代机械锁
  31. 多孔材料    —— 利用多孔结构减重储料 / 海绵吸附液体
```

## ⚠️ 当前限制

qwen2.5:3b 在“把自由表述映射到 39 个标准参数”这一步仍是瓶颈：
30 条主评测集可到 100%，但 10 条未参与调参的留出集只有 40%。
若要把泛化准确率稳定做到 80% 以上，优先换用 qwen2.5:7b/14b 或更大的模型。

## 📄 License

MIT License
