import streamlit as st
from openai import OpenAI
import os

# --- 页面基础配置 ---
st.set_page_config(
    page_title="YSU 教务问答助手 (AutoDL版)",
    page_icon="🎓",
    layout="wide"
)

# --- 侧边栏配置 ---
with st.sidebar:
    st.title("⚙️ 模型配置")
    st.info("后端连接: AutoDL 本地 API")
    
    api_host = st.text_input("API 地址", "http://localhost:8000/v1")
    model_name = st.text_input("模型名称", "chatglm3")
    
    temperature = st.slider("随机性", 0.0, 1.0, 0.1)
    max_tokens = st.slider("回复长度", 128, 4096, 2048)
    # 强制关闭流式输出开关（用于调试）
    use_stream = st.toggle("开启流式输出 (Stream)", value=False)
    
    if st.button("清除对话历史"):
        st.session_state.messages = []
        st.rerun()

# --- 聊天核心逻辑 ---
st.title("🎓 燕山大学教务智能问答")
st.caption("基于 ChatGLM3-6B + YSU微调模型")

client = OpenAI(api_key="0", base_url=api_host)

# 初始化历史记录（包含欢迎语）
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "同学你好！我是燕山大学教务助手，有什么关于选课、考试或转专业的问题可以问我。"}
    ]

# 渲染界面（保留欢迎语）
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 处理用户输入
if prompt := st.chat_input("请输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # --- 【关键修复】构建发送给 API 的消息列表 ---
        # 过滤掉第一条欢迎语，确保对话以 User 开头
        api_messages = []
        for msg in st.session_state.messages:
            if msg["content"] == "同学你好！我是燕山大学教务助手，有什么关于选课、考试或转专业的问题可以问我。":
                continue
            api_messages.append(msg)
        # -----------------------------------------

        try:
            if use_stream:
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=api_messages, # 使用过滤后的消息列表
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            else:
                # 非流式请求 (最稳妥模式)
                with st.spinner("正在思考中..."):
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=api_messages, # 使用过滤后的消息列表
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=False
                    )
                    full_response = response.choices[0].message.content
                    message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"请求失败: {e}")
