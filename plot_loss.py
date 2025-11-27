import json
import matplotlib.pyplot as plt
import os

# 日志文件路径
log_file = "/root/autodl-tmp/ysu_finetuned_model_v2/trainer_log.jsonl"
output_img = "/root/autodl-tmp/training_loss.png"

steps = []
losses = []

if not os.path.exists(log_file):
    print(f"错误：找不到日志文件 {log_file}")
    exit(1)

print(f"正在读取日志：{log_file} ...")

with open(log_file, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            # 提取包含 loss 的记录
            if 'loss' in data:
                # 兼容不同的 step 键名
                step = data.get('step', data.get('current_steps', 0))
                steps.append(step)
                losses.append(data['loss'])
        except Exception as e:
            continue

if not steps:
    print("未找到有效的 Loss 数据！")
    exit(1)

# 绘图
plt.figure(figsize=(12, 6))
plt.plot(steps, losses, label='Training Loss', color='#1f77b4', linewidth=2)
plt.xlabel('Steps', fontsize=12)
plt.ylabel('Loss', fontsize=12)
plt.title('ChatGLM3-6B Fine-tuning Loss Curve (YSU Dataset)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

# 保存图片
plt.savefig(output_img)
print(f"✅ 成功！损失曲线图已保存为：{output_img}")
print("请在左侧文件列表中双击打开查看。")
