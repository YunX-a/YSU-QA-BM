import json

# --- 请确保您的原始文件名与此一致 ---
input_file = 'ysu.json'
output_file = 'ysu_dataset.json'
# ------------------------------------

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print(f"打开或解析 {input_file} 时出错: {e}")
    exit()

formatted_data = []
key_map = {"question": "instruction", "answer": "output"}

for i, item in enumerate(data):
    if not isinstance(item, dict):
        print(f"错误: 第 {i+1} 条数据不是一个有效的JSON对象（字典），内容是: {item}")
        continue

    new_item = {}
    new_item["instruction"] = item.get("question", item.get("instruction", ""))
    new_item["input"] = item.get("input", "")
    new_item["output"] = item.get("answer", item.get("output", ""))

    if not new_item["instruction"] or not new_item["output"]:
        print(f"警告: 第 {i+1} 条数据缺少 'question'/'answer' 或 'instruction'/'output'，已跳过。")
        continue

    formatted_data.append(new_item)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(formatted_data, f, ensure_ascii=False, indent=4)

print(f"处理完成！生成了 {len(formatted_data)} 条标准数据，已保存到 {output_file}")