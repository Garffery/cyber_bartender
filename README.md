# 🍸 Cyber Bartender

Cyber Bartender 是一个基于大语言模型（LLM）的智能调酒师 Agent。它能够与用户进行对话，了解用户的口味偏好（如基酒、口感、烈度等），并基于这些信息搜索和推荐最适合的鸡尾酒。

项目采用前后端分离架构，利用 LangGraph 进行 Agent 流程编排，结合 FastAPI 提供后端服务，使用 Streamlit 构建交互式前端界面。

## ✨ 功能特性

*   **智能对话交互**：通过自然语言与用户沟通，理解复杂需求。
*   **个性化推荐**：根据用户的口味偏好（清爽、浓烈、果味等）推荐定制化鸡尾酒。
*   **实时信息搜索**：集成 Tavily Search API，获取最新的鸡尾酒配方和文化背景。
*   **精美卡片展示**：结构化展示鸡尾酒信息，包括中英文名称、描述、口感、烈度及推荐理由。
*   **人机协同（Human-in-the-loop）**：支持在必要时打断流程，向用户追问更多细节。
*   **前后端分离**：
    *   **Backend**: FastAPI + LangGraph
    *   **Frontend**: Streamlit

## 📂 项目结构

```
cyber_bartender/
├── agent/                  # Agent 核心逻辑
│   ├── cyber_bartender.py  # LangGraph 图定义与编译
│   ├── state.py            # 状态定义 (BartenderState)
│   └── prompts.py          # Prompt 模板
├── backend/                # 后端服务
│   └── server.py           # FastAPI 服务器
├── frontend/               # 前端界面
│   └── app.py              # Streamlit 应用
├── .env                    # 环境变量配置 (需自行创建)
├── requirements.txt        # 项目依赖
└── README.md               # 项目文档
```

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.9+ 或 Anaconda。推荐使用 Conda 创建虚拟环境。

```bash
conda create -n mul-agent python=3.10
conda activate mul-agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

在项目根目录下创建一个 `.env` 文件，并填入以下必要的 API Keys：

```env
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
```

*   **GOOGLE_API_KEY**: 用于访问 Google Gemini 模型。
*   **TAVILY_API_KEY**: 用于 Tavily 搜索服务。

### 4. 启动服务

**启动后端 (FastAPI)**

打开一个新的终端窗口：

```bash
conda activate mul-agent
python backend/server.py
```
后端服务将启动在 `http://localhost:8000`。

**启动前端 (Streamlit)**

打开另一个终端窗口：

```bash
conda activate mul-agent
streamlit run frontend/app.py
```
前端页面将自动在浏览器中打开，地址通常为 `http://localhost:8501`。

## 🛠️ 技术栈

*   **LLM Framework**: [LangChain](https://www.langchain.com/) / [LangGraph](https://langchain-ai.github.io/langgraph/)
*   **Model**: Google Gemini (gemini-2.0-flash-exp)
*   **Search**: [Tavily AI](https://tavily.com/)
*   **Backend**: [FastAPI](https://fastapi.tiangolo.com/)
*   **Frontend**: [Streamlit](https://streamlit.io/)
*   **Logging**: Loguru

## 📝 开发日志

*   构建了基于 LangGraph 的 Agent 工作流。
*   实现了 `BartenderState` 进行状态管理。
*   集成了 Streamlit Chat 界面与自定义 HTML/CSS 组件渲染。
*   解决了前后端通信与异步流式输出问题。
