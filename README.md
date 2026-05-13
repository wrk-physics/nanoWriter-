```markdown
# 📚 小说智能创作助手 —— 基于DeepSeek推理模型的武侠小说自动生成系统

本工具集通过分析参考小说的文风基因，调用大语言模型生成完整的长篇武侠小说大纲、分章详细情节，并逐章自动撰写出符合目标字数与风格要求的正文。全程只需提供一本参考风格的小说原文（`.txt`），其余步骤全自动完成。

## 🚀 快速开始（保姆级步骤）

### 1️⃣ 环境准备（完整教程）

#### 1.1 安装 Python（3.8 或更高版本）
- 访问 [Python 官方网站](https://www.python.org/downloads/)
- 下载适用于你操作系统的 Python 安装包（推荐 3.8～3.11 版本）
- **安装时务必勾选** `Add Python to PATH`（将 Python 添加到环境变量）
- 安装完成后，打开终端（命令提示符 / PowerShell / Git Bash）验证：
  ```bash
  python --version
  ```
  如果显示 `Python 3.x.x` 则成功。

#### 1.2 （推荐）创建虚拟环境
虚拟环境可以隔离项目依赖，避免与其他 Python 项目冲突。
```bash
# 进入项目文件夹
cd /d/虚拟C盘/nanowriter   # 你的实际路径

# 创建虚拟环境（venv 为文件夹名，可随意）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
```
激活后，终端前面会出现 `(venv)` 标识。

#### 1.3 安装依赖库
项目只需要 `requests` 库（用于调用 API）：
```bash
pip install requests
```
如果想快速安装所有常用库，也可以直接执行（可选）：
```bash
pip install requests tqdm
```

#### 1.4 获取 DeepSeek API 密钥
- 访问 [DeepSeek 开放平台](https://platform.deepseek.com/) 注册账号
- 登录后，进入“API Keys”页面
- 点击“创建 API Key”，复制生成的密钥（以 `sk-` 开头）

#### 1.5 设置环境变量（安全存放 API Key）
**不再推荐在代码里直接写密钥**，改用环境变量读取，防止上传 GitHub 时泄露。

- **Windows（永久设置）**：
  1. 打开“系统属性” → “高级” → “环境变量”
  2. 在“用户变量”下点击“新建”
  3. 变量名：`DEEPSEEK_API_KEY`
  4. 变量值：粘贴你的 `sk-xxx` 密钥
  5. 确定，然后**重启终端**生效。

- **Windows（临时设置，仅当前终端有效）**：
  ```cmd
  set DEEPSEEK_API_KEY=sk-你的真实密钥
  ```

- **macOS / Linux（永久设置）**：
  编辑 `~/.bashrc` 或 `~/.zshrc`，添加一行：
  ```bash
  export DEEPSEEK_API_KEY="sk-你的真实密钥"
  ```
  然后执行 `source ~/.bashrc` 或重启终端。

- **macOS / Linux（临时设置）**：
  ```bash
  export DEEPSEEK_API_KEY="sk-你的真实密钥"
  ```

#### 1.6 验证环境配置
在终端中运行 Python，尝试导入 requests 并读取环境变量：
```python
python -c "import requests; import os; print(os.getenv('DEEPSEEK_API_KEY', '未设置'))"
```
如果正确输出你的密钥（或以 `sk-` 开头的内容），说明环境配置成功。按 `Ctrl+Z`（Windows）或 `Ctrl+D`（Mac/Linux）退出 Python。

---

### 2️⃣ 准备参考文本（任意小说均可）
项目会自动提取文本的文风特征，**不限于《雪中悍刀行》**。你只需将任意一部小说的纯文本文件（`utf-8` 编码）命名为 **`xuezhong.txt`**，放入项目根目录即可。例如：
- 想模仿金庸风格 → 将《天龙八部》的文本保存为 `xuezhong.txt`
- 想模仿古龙风格 → 将《多情剑客无情剑》的文本保存为 `xuezhong.txt`
- 仍想模仿《雪中悍刀行》 → 同样命名为 `xuezhong.txt`

> 请确保你有权使用该文本，仅用于个人学习。

---

### 3️⃣ 提取文风基因库
运行 `extract_style_genome.py`，它会将 `xuezhong.txt` 切块并逐块分析，最终生成 `style_genome.md`（包含词汇句式、描写手法等规则）。
```bash
python extract_style_genome.py
```
- ⏱️ 耗时取决于文本长度，一般需要几分钟。
- 如果中途报错网络问题，重试即可；脚本会跳过错误块继续处理。
- 最终会生成 `raw_features.txt`（原始特征）和 `style_genome.md`。

---

### 4️⃣ 生成小说大纲
**无需修改任何代码**（脚本会自动读取环境变量 `DEEPSEEK_API_KEY`）。直接执行：
```bash
python outline_generator.py
```
- 脚本会调用 DeepSeek 推理模型（`deepseek-reasoner`）生成完整大纲，包含：
  - 小说名、500字梗概
  - 4卷 × 40章 = 160章的详细情节（每章约200字）
  - 12个原创人物设定
  - 5条伏笔设计
- 生成耗时约 3~5 分钟，结果保存在 **`novel_outline.md`**。

---

### 5️⃣ 解析大纲为 JSON 格式
```bash
python parse_outline_to_json.py
```
- 该脚本会读取 `novel_outline.md`，提取每章的核心情节，保存为 **`chapter_plots.json`**（形如 `{"1-1": "开篇情节...", "1-2": "..."}`）。
- 控制台会输出提取的章节数量。

---

### 6️⃣ 初始化写作状态
```bash
python init_state_from_outline.py
```
- 从 `novel_outline.md` 中读取“主要人物”和“贯穿全书的伏笔”，生成 **`novel_state.json`**（记录已完成章节、摘要、伏笔列表等）。
- 该文件会被主程序用来追踪写作进度。

---

### 7️⃣ 开始逐章写作
**再次确认环境变量 `DEEPSEEK_API_KEY` 已正确设置**，然后运行：
```bash
python chapter_writer_v4.py
```
- 程序会自动：
  - 读取大纲、状态、文风基因库
  - 从第一卷第1章开始，按顺序生成正文（每章约6200字）
  - 每写完一章，立即保存到 `novel_output/第X卷/chapter_XX.txt`
  - 更新状态文件，生成摘要，记录费用
  - 如果中途中断，再次运行会从断点处继续续写

- **控制台输出示例**：
  ```
  📖 《青冥浩荡》
  ▶ 从第1卷第1章开始续写...
  ========================================
  ▶ 第1卷 第1章 开始
     上下文大小: 28900 字符 ≈ 19267 tokens (全文3章)
     ⏳ 调用深度推理模型生成正文...
     ✅ 已保存 novel_output/第1卷/chapter_01.txt（耗时 45.2s）
     本章费用约 ¥0.0523，累计 ¥0.0523
     进度：1/160 章
  ```

- **总耗时预估**：每章生成约40~60秒，160章全部完成大约需要 **2~3小时**（取决于 API 速率）。

---

### 8️⃣ 查看成果
- 正文文件位于 `novel_output/第1卷/` … `第4卷/` 目录下，每章一个 `.txt` 文件。
- 日志文件 `writing_log.txt` 记录了每章的生成时间、字数、耗时。
- 费用记录 `total_cost.txt` 累计了所有 API 调用成本（按官方定价估算）。

## 📁 项目文件结构

```
项目根目录/
│
├── xuezhong.txt                # 【用户准备】风格参考小说原文（任意小说皆可）
├── extract_style_genome.py     # 步骤3：提取文风基因
├── outline_generator.py        # 步骤4：生成大纲
├── parse_outline_to_json.py    # 步骤5：解析大纲为 JSON
├── init_state_from_outline.py  # 步骤6：初始化状态文件
├── chapter_writer_v4.py        # 步骤7：主写作程序
├── prepare_data.py             # （可选）生成模拟训练数据，本项目中无需运行
│
├── style_genome.md             # 自动生成的文风规则
├── novel_outline.md            # 自动生成的大纲（Markdown）
├── chapter_plots.json          # 自动生成的章节梗概字典
├── novel_state.json            # 自动生成的写作状态
├── writing_log.txt             # 自动生成的日志
├── total_cost.txt              # 自动生成的累计费用
│
└── novel_output/               # 生成的正文目录
    ├── 第1卷/
    │   ├── chapter_01.txt
    │   ├── chapter_02.txt
    │   └── ...
    ├── 第2卷/
    ├── 第3卷/
    └── 第4卷/
```

## ⚙️ 核心参数调整（可选）

如果你希望修改生成字数、上下文长度等，可以编辑 `chapter_writer_v4.py` 开头的配置：

```python
MAX_FULL_CHAPTERS = 40      # 每次请求带给AI的最近完整章数（越大上下文越重，但一致性更好）
TARGET_CHAPTER_WORDS = 6200 # 每章目标字数（可根据需要调整，推荐4000~8000）
MAX_CONTEXT_TOKENS = 900000 # 上下文 token 上限（DeepSeek 最大支持 1M，保持默认即可）
```

## 🛠️ 常见问题与解决

### ❌ 运行脚本时提示 `ModuleNotFoundError: No module named 'requests'`
→ 没有安装依赖库。执行 `pip install requests` 即可。

### ❌ 提示 `DEEPSEEK_API_KEY` 环境变量未设置
→ 请按照 **步骤 1.5** 正确设置环境变量，并重启终端后再运行脚本。

### ❌ API 请求失败，状态码 401
→ 检查 API Key 是否正确（以 `sk-` 开头），账号是否有余额（新用户有赠送额度）。

### ❌ 生成章节时卡住或超时
→ 网络波动时脚本会自动重试 3 次，若仍失败会跳过本章。重启 `chapter_writer_v4.py` 会自动从最新进度继续。

### ❌ 章节内容出现重复或逻辑断裂
→ 可以适当增加 `MAX_FULL_CHAPTERS` 的值（如设为 60），让 AI 看到更多前文。这会略微增加输入 token 费用（输入远比输出便宜，影响不大）。

### ❌ 我想换一本参考小说（任意风格都可以吗？）
→ **是的，完全可以。** 直接将你要模仿风格的小说文本文件命名为 `xuezhong.txt`（UTF-8 编码），然后重新运行 `extract_style_genome.py` 即可自动提取新风格。整个项目不依赖特定小说，任何小说都可以作为风格来源。

### ❌ 不想使用推理模型，想换成普通对话模型
→ 修改 `outline_generator.py` 和 `chapter_writer_v4.py` 中的 `"model"` 字段为 `"deepseek-chat"`（但推理模型对长剧情一致性更好）。

## 📜 许可证与免责
- 本工具仅供个人学习、创作辅助使用。
- 生成的小说版权归使用者所有，但请勿直接抄袭参考文本的具体情节。
- DeepSeek API 的使用请遵守其服务条款。

---

**完成上述 8 个步骤后，你将得到一部 160 章、约 100 万字的完整武侠小说！** 祝你创作愉快 ✍️
```
