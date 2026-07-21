# 🧠 TRIZ 智能体 · 本地化AI创新助手

基于 **TRIZ 方法论 + 本地大模型** 的技术矛盾自动提取与解决方案推荐系统。

## ✨ 功能特性

- 🔍 **矛盾提取**：输入技术需求，自动提取改善/恶化参数
- 🧠 **本地大模型**：基于 Ollama + Qwen2.5，无需 API Key
- 📐 **矛盾矩阵**：216+ 条 TRIZ 映射关系，自动推荐发明原理
- 📋 **历史记录**：自动保存所有分析记录，支持搜索
- 🌐 **Web 界面**：开箱即用的可视化操作界面

## 🏗️ 技术架构

| 组件 | 技术 |
|------|------|
| 前端 | HTML + CSS + JavaScript |
| 后端 | FastAPI (Python) |
| 大模型 | Ollama + Qwen2.5:3B |
| 知识库 | TRIZ 矛盾矩阵 (JSON) |
| 数据库 | SQLite |

## 📦 快速开始

1. 克隆项目
git clone https://github.com/Aurora-dark/triz-agent.git
cd triz-agent

2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows

3. 安装依赖
pip install -r requirements.txt

4. 安装 Ollama 并下载模型
ollama pull qwen2.5:3b

5. 启动服务
python run.py

6. 访问界面
打开浏览器：http://127.0.0.1:8000

📁 项目结构
triz-agent/
├── api/            # 后端 API
├── data/           # TRIZ 知识库
├── frontend/       # 前端界面
├── storage/        # 数据存储
├── run.py          # 启动入口
└── requirements.txt

📝 使用示例
输入：手机屏幕更大但单手不好拿
输出：
改善参数：5. 运动物体的面积
恶化参数：33. 可操作性
推荐方案：分割、局部质量、合并/组合、重量补偿
<img width="830" height="962" alt="458b2e70e2ca25aae20d982134df793d" src="https://github.com/user-attachments/assets/14467f1d-2adf-4b24-8d1b-41edf1b79094" />

📄 License
MIT License
