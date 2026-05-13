import requests, os, sys, json, time, re, shutil

os.environ['PYTHONUTF8'] = '1'
sys.stdout.reconfigure(encoding='utf-8')

# ==================== 配置 ====================
API_KEY = "sk-"          # ← 替换成真实 Key
BASE_URL = "https://api.deepseek.com/v1/chat/completions"
OUTPUT_ROOT = "novel_output"
LOG_FILE = "writing_log.txt"
COST_FILE = "total_cost.txt"
STATE_FILE = "novel_state.json"

MAX_FULL_CHAPTERS = 40                # 最近N章全文
MAX_CONTEXT_TOKENS = 900_000          # 上下文上限 (token)
TARGET_CHAPTER_WORDS = 6200           # 每章目标字数

# ==================== 加载基础资源 ====================
print("📂 加载基础文件...")
with open("style_genome.md", "r", encoding="utf-8") as f:
    genome = f.read()
with open("novel_outline.md", "r", encoding="utf-8") as f:
    outline = f.read()
with open("chapter_plots.json", "r", encoding="utf-8") as f:
    PLOTS = json.load(f)

novel_name = re.search(r'#\s*(.+?)\n', outline)
novel_name = novel_name.group(1) if novel_name else "无名"
print(f"📖 《{novel_name}》")

# 初始化状态文件
if not os.path.exists(STATE_FILE):
    print("❌ 缺少 novel_state.json，请先运行 init_state_from_outline.py")
    sys.exit(1)

with open(STATE_FILE, "r", encoding="utf-8") as f:
    state = json.load(f)

# 自动修复已完成列表（检查实际文件是否存在）
valid_completed = []
for item in state.get("completed", []):
    v_str, c_str = item.split('-')
    filepath = os.path.join(OUTPUT_ROOT, f"第{v_str}卷", f"chapter_{int(c_str):02d}.txt")
    if os.path.exists(filepath):
        valid_completed.append(item)
    else:
        print(f"⚠️ 发现状态记录 {item} 但文件缺失，已移除")
state["completed"] = valid_completed
with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

# 初始化费用记录
if not os.path.exists(COST_FILE):
    with open(COST_FILE, "w") as f:
        f.write("0")

# ==================== API 调用 ====================
SYSTEM = f"""你是武侠小说宗师，正在创作《{novel_name}》。你必须：
1. 完全遵循下文提供的《文风基因库》和《全书大纲》。
2. 阅读所有已写章节（完整正文或详细摘要），确保人物、对话、伏笔、文风完全延续。
3. 每章结尾自然过渡，为下一章埋下悬念。
4. 绝不改变已设定的角色姓名、性格、关系。
{genome}
"""

def chat(messages, max_retries=3):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "deepseek-reasoner",
        "messages": messages,
        "stream": False
    }
    for attempt in range(1, max_retries+1):
        try:
            r = requests.post(BASE_URL, headers=headers, json=payload, timeout=600)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            else:
                print(f"⚠️ HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"⚠️ 网络错误 (尝试{attempt}/{max_retries}): {e}")
            time.sleep(10)
    return None

# ==================== 上下文构建 ====================
def build_context(vol, ch, state):
    parts = []
    # 完整大纲与人物
    parts.append("# 全书大纲（必须严格遵循）\n" + outline + "\n")
    parts.append(f"## 核心人物设定\n{state.get('characters','')}\n")
    parts.append(f"## 活跃伏笔\n{chr(10).join(state.get('foreshadowing',[]))}\n")

    # 已写章节
    completed = state.get("completed", [])
    chapters_data = []  # (vol, ch, text, summary)
    for item in completed:
        v, c = map(int, item.split('-'))
        filepath = os.path.join(OUTPUT_ROOT, f"第{v}卷", f"chapter_{c:02d}.txt")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            # 从 PLOTS 获取原始梗概，若缺失则取前200字
            summary = PLOTS.get(f"{v}-{c}", text[:200])
            chapters_data.append((v, c, text, summary))
        else:
            # 文件丢失，使用梗概兜底
            summary = PLOTS.get(f"{v}-{c}", "（内容缺失）")
            chapters_data.append((v, c, "[文件丢失]", summary))

    total = len(chapters_data)
    # 决定显示全文的章数（最近N章，但需动态调整以不超限）
    full_count = min(MAX_FULL_CHAPTERS, total)
    while full_count > 0:
        # 估算当前配置下的 token
        early_summaries = "\n".join([f"第{v}卷第{c}章摘要：{summary}" for v,c,_,summary in chapters_data[:total-full_count]])
        recent_full = "\n\n".join([f"===== 第{v}卷第{c}章 =====\n{text}" for v,c,text,_ in chapters_data[total-full_count:]])
        test_context = "\n".join([parts[0], parts[1], parts[2], "\n## 早期章节摘要\n"+early_summaries, "\n## 近期章节全文\n"+recent_full])
        est_tokens = len(test_context) / 1.5
        if est_tokens <= MAX_CONTEXT_TOKENS:
            break
        full_count -= 1  # 自动减少全文章数
    if full_count == 0:
        full_count = 1  # 至少保留上一章全文

    # 早期章节以详细摘要呈现
    if total > full_count:
        parts.append("## 早期章节详细摘要（已浓缩关键情节）\n")
        for v, c, text, summary in chapters_data[:total-full_count]:
            # 使用原始梗概作为摘要，确保关键信息不丢
            parts.append(f"第{v}卷第{c}章：{summary}\n")
        parts.append("\n")

    # 近期章节全文
    if full_count > 0:
        parts.append(f"## 最近{full_count}章完整正文（必须仔细阅读）\n")
        for v, c, text, _ in chapters_data[total-full_count:]:
            parts.append(f"\n===== 第{v}卷第{c}章 =====\n{text}\n")

    # 创作指令
    chapter_plot = PLOTS.get(f"{vol}-{ch}", "根据上下文自由发展")
    parts.append(f"\n## 本章创作指令\n请撰写《{novel_name}》第{vol}卷第{ch}章，字数约{TARGET_CHAPTER_WORDS}字。\n核心情节：{chapter_plot}\n")
    parts.append("务必：\n1. 严格延续上一章的结尾\n2. 保持人物言行一致\n3. 推进或揭示伏笔\n4. 结尾留下合理悬念\n")

    context = '\n'.join(parts)
    est_tokens = len(context) / 1.5
    print(f"   上下文大小: {len(context)} 字符 ≈ {est_tokens:.0f} tokens (全文{full_count}章)")
    return context, full_count

# ==================== 主循环 ====================
TOTAL_VOLS = 4
CHAPTERS_PER_VOL = 40

# 寻找起始章节
start_vol, start_ch = 1, 1
for vol in range(1, TOTAL_VOLS+1):
    for ch in range(1, CHAPTERS_PER_VOL+1):
        if f"{vol}-{ch}" not in state["completed"]:
            start_vol, start_ch = vol, ch
            break
    else:
        continue
    break
else:
    print("🎉 所有章节已完成！")
    sys.exit(0)

print(f"▶ 从第{start_vol}卷第{start_ch}章开始续写...")

for vol in range(start_vol, TOTAL_VOLS+1):
    vol_dir = os.path.join(OUTPUT_ROOT, f"第{vol}卷")
    os.makedirs(vol_dir, exist_ok=True)

    ch_start = start_ch if vol == start_vol else 1
    for ch in range(ch_start, CHAPTERS_PER_VOL+1):
        print(f"\n{'='*40}\n▶ 第{vol}卷 第{ch}章 开始")
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)

        context, used_full = build_context(vol, ch, state)
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": context}]

        # 记录开始时间
        start_time = time.time()
        print("   ⏳ 调用深度推理模型（DeepSeek-Reasoner）生成正文...")
        chapter_text = chat(messages)
        elapsed = time.time() - start_time

        if not chapter_text:
            print("❌ 生成失败，跳过本章（可重启续写）")
            continue

        # 写入临时文件，成功后再重命名（防止中断损坏）
        filename = f"chapter_{ch:02d}.txt"
        tmp_filepath = os.path.join(vol_dir, filename + ".tmp")
        final_filepath = os.path.join(vol_dir, filename)
        with open(tmp_filepath, "w", encoding="utf-8") as f:
            f.write(chapter_text)
        os.replace(tmp_filepath, final_filepath)   # 原子操作
        print(f"   ✅ 已保存 {final_filepath}（耗时 {elapsed:.1f}s）")

        # 生成摘要
        print("   📝 生成摘要...")
        summ_prompt = f"为下面章节写80字摘要，格式：\n摘要：\n人物变化：\n新伏笔：\n揭开伏笔：\n章节：{chapter_text[:4000]}"
        summ = chat([{"role": "system", "content": "你是文学助手。"}, {"role": "user", "content": summ_prompt}])
        summary = summ.split("摘要：")[-1].split("\n")[0] if summ else chapter_text[:80]

        # 更新状态
        state["completed"].append(f"{vol}-{ch}")
        state["summaries"].append(summary)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        # 写入日志
        word_count = len(chapter_text)
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"{time.ctime()} | Vol.{vol} Ch.{ch} | Words:{word_count} | Time:{elapsed:.0f}s | FullCtx:{used_full}ch\n")

        # 粗略成本更新（按 6元/百万输出token 计算，输入约 0.1元/百万token）
        output_tokens = word_count * 1.5  # 估算
        input_tokens = len(context) / 1.5
        cost = (input_tokens / 1_000_000) * 0.1 + (output_tokens / 1_000_000) * 6
        with open(COST_FILE, "r") as f:
            total_cost = float(f.read().strip())
        total_cost += cost
        with open(COST_FILE, "w") as f:
            f.write(f"{total_cost:.4f}")
        print(f"   本章费用约 ¥{cost:.4f}，累计 ¥{total_cost:.4f}")

        print(f"   进度：{len(state['completed'])}/160 章")

print(f"\n🎉 全书生成完毕！总费用约 ¥{total_cost:.4f}，日志见 {LOG_FILE}")