import requests, re

API_KEY = "sk-"
BASE_URL = "https://api.deepseek.com/v1/chat/completions"

def deepseek_chat(messages, temp=0.3):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": temp,
        "stream": False
    }
    r = requests.post(BASE_URL, headers=headers, json=payload)
    return r.json()["choices"][0]["message"]["content"]

# 1. 切块——每块8000字，重叠500字避免断句
with open("xuezhong.txt", "r", encoding="utf-8") as f:
    full_text = f.read().replace('\r', '\n')

chunk_size = 8000
overlap = 500
chunks = []
start = 0
while start < len(full_text):
    end = min(start + chunk_size, len(full_text))
    chunks.append(full_text[start:end])
    start += chunk_size - overlap

print(f"共切分 {len(chunks)} 个块，开始逐一提取风格特征...")

# 2. 逐块提取
style_features = []
for i, chunk in enumerate(chunks):
    prompt = f"""下面是一段小说的原文。请仔细分析其文风，提炼出至少10条具体的风格特征（用词、句式、节奏、描写手法、对话风格、叙事视角等）。每条特征用一句话描述，尽量客观，不要评价好坏。

原文：
{chunk}
"""
    messages = [
        {"role": "system", "content": "你是文学风格分析专家，擅长提取文本风格特征。"},
        {"role": "user", "content": prompt}
    ]
    try:
        response = deepseek_chat(messages)
        features = [line.strip('- ') for line in response.split('\n') if line.strip()]
        style_features.extend(features)
        print(f"块 {i+1}/{len(chunks)} 完成，提取 {len(features)} 条特征")
    except Exception as e:
        print(f"块 {i+1} 出错：{e}，跳过")
        continue

# 3. 去重重写（用DeepSeek再做一次整理）
unique_features = list(set(style_features))
with open("raw_features.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(unique_features))

print("原始特征已保存，正在整理成最终基因库...")

clean_prompt = f"""以下是提取自小说《雪中悍刀行》的大量风格特征（可能重复）。请将它们整理成一份精炼的《文风基因库》，要求：
1. 分类为：词汇句式、描写手法、叙事技巧、对话风格、节奏控制等。
2. 每个类别下列出最具代表性的规则（去重合并），保持具体，避免空泛。
3. 最后给出一个“写作禁忌清单”。
4. 用Markdown格式输出。

特征列表：
{open('raw_features.txt', 'r', encoding='utf-8').read()}
"""

final_genome = deepseek_chat([
    {"role": "system", "content": "你是顶尖文学编辑，擅长概括写作风格。"},
    {"role": "user", "content": clean_prompt}
], temp=0.5)

with open("style_genome.md", "w", encoding="utf-8") as f:
    f.write(final_genome)

print("✅ 文风基因库已保存至 style_genome.md")