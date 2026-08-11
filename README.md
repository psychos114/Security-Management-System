\# 医院物业安管 Agentic RAG 系统



这是一个前后端分离的医院物业安管知识助手学习项目。



系统使用 React、FastAPI、SQLite、FAISS、ModelScope Embedding

和 DeepSeek 工具调用，实现基于内部知识库的 Agentic RAG 问答。



\## 主要功能



\- 医院突发事件处置知识问答

\- 安管巡检知识检索

\- 投诉SLA和超时升级知识问答

\- 深圳消防资料检索

\- FAISS语义检索

\- SQLite FTS5关键词检索

\- RRF混合排序

\- Agent自主调用检索工具

\- 根据doc\_code读取完整资料

\- 固定资料编号引用

\- React问答页面

\- 工具执行轨迹展示

\- 人工确认和安全提醒



\## 技术栈



\### 前端



\- React

\- Vite

\- Axios



\### 后端



\- Python

\- FastAPI

\- SQLite

\- FAISS

\- OpenAI兼容工具调用接口



\### AI接口



\- DeepSeek：对话和Agent工具调用

\- ModelScope：知识向量生成



\## 项目结构



```text

Security\_Management\_System

├─ backend

│  └─ app

│     ├─ agentic\_rag

│     ├─ api

│     ├─ core

│     ├─ db

│     ├─ schemas

│     ├─ services

│     └─ main.py

├─ database

│  ├─ knowledge\_documents

│  ├─ build\_database.py

│  └─ security\_management\_demo.db

├─ frontend

│  ├─ src

│  └─ package.json

├─ .env.example

├─ .gitignore

├─ requirements.txt

└─ README.md

