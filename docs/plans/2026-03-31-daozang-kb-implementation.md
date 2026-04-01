# 道藏知识可视化 Demo Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个具备真实抓取、自动标注、图谱生成和静态前端展示能力的道藏知识可视化 Demo。

**Architecture:** 使用 Python 离线数据管线生成 `archive/`、`chapter_md/`、`kg/`、`data/`，再由 `docs/` 静态页面消费 JSON。核心逻辑集中在 `src/daozang_kb` 包中，数字脚本仅作为 CLI 入口。

**Tech Stack:** Python 3.13、标准库 unittest、纯 HTML/CSS/JS、D3.js v7 CDN。

---

### Task 1: 建立工程骨架与测试入口

**Files:**
- Create: `CLAUDE.md`
- Create: `README.md`
- Create: `.gitignore`
- Create: `serve.sh`
- Create: `src/daozang_kb/__init__.py`
- Create: `tests/test_annotation.py`
- Create: `tests/test_validation.py`
- Create: `tests/test_graphs.py`

**Step 1: Write the failing tests**

- 为标注恢复文本、PN 连续性校验、概念图共现构建编写失败测试。

**Step 2: Run test to verify it fails**

Run: `cd daozang-kb && python3 -m unittest discover -s tests -v`

Expected: 因模块不存在或函数缺失而失败。

**Step 3: Write minimal implementation**

- 创建包入口与最小可导入结构。

**Step 4: Run test to verify it passes**

Run: `cd daozang-kb && python3 -m unittest discover -s tests -v`

Expected: 至少导入层错误消失，剩余测试进入真实实现失败阶段。

### Task 2: 实现抓取与切分管线

**Files:**
- Create: `src/daozang_kb/config.py`
- Create: `src/daozang_kb/fetchers.py`
- Create: `scripts/01_fetch_ctext.py`
- Create: `scripts/02_split_chapters.py`

**Step 1: Write the failing test**

- 为《道德经》 API 响应解析、《庄子》页面正文提取、章节文件格式编写测试。

**Step 2: Run test to verify it fails**

Run: `cd daozang-kb && python3 -m unittest tests.test_annotation tests.test_graphs -v`

Expected: 解析函数缺失或返回值不符。

**Step 3: Write minimal implementation**

- 实现混合抓取策略。
- 生成 `archive/daodejing/ctext_raw.txt` 与 `archive/nanhua/ctext_raw.txt`。
- 生成 `archive/.../chapters/*.txt`。

**Step 4: Run test to verify it passes**

Run: `cd daozang-kb && python3 -m unittest discover -s tests -v`

Expected: 抓取解析相关测试通过。

### Task 3: 实现编号、标注与校验

**Files:**
- Create: `src/daozang_kb/annotation.py`
- Create: `src/daozang_kb/validation.py`
- Create: `scripts/03_annotate.py`
- Create: `scripts/08_validate.py`

**Step 1: Write the failing test**

- 为最长匹配标注、去标记恢复原文、PN 连续性和 fable 区块提取编写失败测试。

**Step 2: Run test to verify it fails**

Run: `cd daozang-kb && python3 -m unittest discover -s tests -v`

Expected: 标注与校验测试失败。

**Step 3: Write minimal implementation**

- 生成 `chapter_md/*.tagged.md`。
- 对《道德经》全量和《南华真经》内篇 7 篇自动标注。
- 输出 Markdown 校验报告。

**Step 4: Run test to verify it passes**

Run: `cd daozang-kb && python3 -m unittest discover -s tests -v`

Expected: 标注与校验相关测试通过。

### Task 4: 实体索引与图谱数据

**Files:**
- Create: `src/daozang_kb/graphs.py`
- Create: `scripts/04_build_entity_index.py`
- Create: `scripts/05_build_concept_graph.py`
- Create: `scripts/06_build_fable_graph.py`
- Create: `scripts/07_render_html.py`
- Create: `scripts/ima_verify.py`

**Step 1: Write the failing test**

- 为实体聚合、概念共现边、寓言区块构图、reader 片段化渲染编写失败测试。

**Step 2: Run test to verify it fails**

Run: `cd daozang-kb && python3 -m unittest discover -s tests -v`

Expected: 图谱与导出测试失败。

**Step 3: Write minimal implementation**

- 生成 `kg/entities/entity_index.json`
- 生成 `data/daodejing/*.json`
- 生成 `data/nanhua/*.json`
- 输出 `collation_reports/ima_verify_report.md`

**Step 4: Run test to verify it passes**

Run: `cd daozang-kb && python3 -m unittest discover -s tests -v`

Expected: 图谱构建测试通过。

### Task 5: 实现静态前端与发布

**Files:**
- Create: `docs/index.html`
- Create: `docs/404.html`
- Create: `docs/css/daozang.css`
- Create: `docs/js/shared.js`
- Create: `docs/concept-map/index.html`
- Create: `docs/concept-map/concept-map.js`
- Create: `docs/fable-atlas/index.html`
- Create: `docs/fable-atlas/fable-atlas.js`
- Create: `docs/reader/index.html`
- Create: `docs/reader/reader.js`
- Create: `scripts/sync_to_docs.sh`

**Step 1: Write the failing test**

- 以前端依赖的 JSON 是否存在、`docs/data` 是否同步成功、核心页面是否引用正确脚本作为发布验证的失败测试。

**Step 2: Run test to verify it fails**

Run: `cd daozang-kb && python3 -m unittest discover -s tests -v`

Expected: 发布相关断言失败。

**Step 3: Write minimal implementation**

- 完成三个页面和共享样式/脚本。
- 实现数据同步脚本。

**Step 4: Run test to verify it passes**

Run: `cd daozang-kb && python3 -m unittest discover -s tests -v`

Expected: 测试通过。

### Task 6: 运行全量生成与验证

**Files:**
- Modify: `README.md`

**Step 1: Run pipeline**

Run:

```bash
cd daozang-kb
python3 scripts/01_fetch_ctext.py
python3 scripts/02_split_chapters.py
python3 scripts/03_annotate.py
python3 scripts/04_build_entity_index.py
python3 scripts/05_build_concept_graph.py
python3 scripts/06_build_fable_graph.py
python3 scripts/07_render_html.py
python3 scripts/ima_verify.py || true
bash scripts/sync_to_docs.sh
python3 scripts/08_validate.py
```

**Step 2: Verify**

Run:

```bash
cd daozang-kb
python3 -m unittest discover -s tests -v
python3 scripts/08_validate.py
```

Expected: 单元测试通过，校验报告输出且主流程成功生成发布资源。
