# YSU 教务智能问答大模型 (YSU-QA-BM)

基于 ChatGLM3-6B 和 LoRA 微调技术，专为燕山大学教务场景定制的智能问答助手。

## 🚀 项目简介

本项目在 AutoDL 算力云上进行训练和部署，使用 `LLaMA-Factory` 进行微调，并集成了 `vLLM` 推理加速与 `Streamlit` 前端交互界面。

## 📂 目录结构

- `app.py`: Streamlit 前端 Web 界面代码
- `ysu.json`: 微调数据集
- `download.py`: 模型下载脚本
- `README.md`: 项目说明

## 🛠️ 快速开始

### 1. 环境安装
推荐使用 `uv` 进行包管理：
\`\`\`bash
source vllm_env/bin/activate
pip install -r requirements.txt
\`\`\`

### 2. 下载模型
运行脚本从 ModelScope 下载 ChatGLM3-6B：
\`\`\`bash
python download.py
\`\`\`

### 3. 启动服务
首先启动后端 API：
\`\`\`bash
CUDA_VISIBLE_DEVICES=0 API_PORT=8000 llamafactory-cli api \
    --model_name_or_path /root/autodl-tmp/ysu_merged_model \
    --template chatglm3 \
    --finetuning_type full \
    --infer_backend huggingface
\`\`\`

然后启动前端页面：
\`\`\`bash
streamlit run app.py --server.port 6006
\`\`\`

## 📊 微调细节
- **基座模型**: ChatGLM3-6B
- **微调方式**: LoRA
- **数据集**: ysu.json (燕大教务问答数据)

