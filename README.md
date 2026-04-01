# 道藏知识可视化 Demo

一个面向 GitHub Pages 的纯静态知识可视化项目，处理《道德经》81 章与《南华真经》33 篇，输出可交互的概念星图、寓言图鉴与阅读器。

## 当前范围

- 《道德经》81 章：全量抓取、编号、自动标注、概念图谱。
- 《南华真经》33 篇：全量抓取与编号，内篇 7 篇自动标注与寓言图谱。
- IMA 知识库：辅助校验报告。

## 目录

- `archive/`：不可变底本
- `chapter_md/`：带 Purple Number 和实体标注的工作文本
- `kg/`：本体、实体索引、关系
- `data/`：前端消费的 JSON
- `docs/`：GitHub Pages 发布目录
- `scripts/`：离线生成脚本
- `src/daozang_kb/`：核心 Python 包

## 运行顺序

```bash
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

## 本地预览

```bash
bash serve.sh
```

默认地址：`http://localhost:8080`

如果 `8080` 已被占用，可以直接换端口：

```bash
bash serve.sh 8081
```
