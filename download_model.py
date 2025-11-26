from modelscope import snapshot_download
# 下载到数据盘
model_dir = snapshot_download('ZhipuAI/chatglm3-6b', cache_dir='/root/autodl-tmp')
print("模型已下载至:", model_dir)