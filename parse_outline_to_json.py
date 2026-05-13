import re, json

def parse_outline_detailed(md_path, output_json="chapter_plots.json"):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    chapters = {}
    current_vol = None
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 识别卷标题：## 第一卷 卷名
        vol_match = re.match(r'#+\s*第([一二三四五六七八九十]+)卷', line)
        if vol_match:
            chinese = vol_match.group(1)
            mapping = {'一':'1','二':'2','三':'3','四':'4','五':'5','六':'6','七':'7','八':'8','九':'9','十':'10'}
            current_vol = mapping.get(chinese, chinese)
            i += 1
            continue

        # 匹配章节行：可能以 ###、-、数字等开头，例如 "### 第1章 章名 —— 核心情节"
        if current_vol:
            chap_match = re.match(r'[-#*\s]*第(\d+)章\s*[：:]?\s*(.*)', line)
            if chap_match:
                ch_num = chap_match.group(1)
                first_part = chap_match.group(2).strip()

                # 收集核心情节（可能跨多行）
                plot_parts = []
                # 先看当前行有没有分隔符之后的内容
                for sep in ['——', '：', ':', '- ']:
                    if sep in first_part:
                        plot_start = first_part.split(sep, 1)[-1].strip()
                        plot_parts.append(plot_start)
                        break
                else:
                    # 没有分隔符，整行作为情节开始
                    plot_parts.append(first_part)

                # 继续向下读取，直到遇到空行、下一章或卷标题
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:   # 空行停止
                        break
                    if re.match(r'[-#*\s]*第\d+章', next_line):  # 下一章
                        break
                    if re.match(r'#+\s*第[一二三四五六七八九十]+卷', next_line):  # 下一卷
                        break
                    # 继续追加到情节中
                    plot_parts.append(next_line)
                    j += 1

                full_plot = ' '.join(plot_parts).strip()
                key = f"{current_vol}-{ch_num}"
                chapters[key] = full_plot
                i = j   # 跳过已处理的行
                continue

        i += 1

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)
    print(f"✅ 解析完成，共提取 {len(chapters)} 条详细章节梗概，保存至 {output_json}")

if __name__ == "__main__":
    parse_outline_detailed("novel_outline.md")