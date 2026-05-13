import re, json

def extract_section(text, section_title):
    """
    提取从指定标题开始到下一个 ## 或 # 标题之前的所有内容。
    返回去除了标题行的纯文本。
    """
    pattern = rf'##\s*{section_title}\s*\n(.*?)(?=\n##\s|\n#\s|\Z)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def init_detailed_state(md_path="novel_outline.md", out_json="novel_state.json"):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 提取人物区块（完整保留）
    characters_block = extract_section(text, "主要人物")
    # 提取伏笔区块
    foreshadowing_block = extract_section(text, "贯穿全书的伏笔")

    # 将伏笔区块拆分成单独的伏笔条目（按行拆分，忽略空行和序号）
    foreshadowing_list = []
    for line in foreshadowing_block.split('\n'):
        line = line.strip()
        if not line:
            continue
        # 去除开头的序号、符号
        cleaned = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()
        if cleaned:
            foreshadowing_list.append(cleaned)

    # 如果没有伏笔，给个占位
    if not foreshadowing_list:
        foreshadowing_list = ["待补充"]

    initial_state = {
        "completed": [],
        "summaries": [],
        "foreshadowing": foreshadowing_list,
        "characters": characters_block if characters_block else "待补充"
    }

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(initial_state, f, ensure_ascii=False, indent=2)

    print(f"✅ novel_state.json 已自动生成（详细模式）")
    print(f"   - 人物设定：{len(characters_block)} 字符")
    print(f"   - 伏笔数量：{len(foreshadowing_list)} 条")

if __name__ == "__main__":
    init_detailed_state()