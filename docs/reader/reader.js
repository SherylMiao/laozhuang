const { copyText, fetchJSON, navigateTo, renderRichText } = window.DaozangShared;

const titleEl    = document.querySelector("#reader-title");
const subtitleEl = document.querySelector("#reader-subtitle");
const proseEl    = document.querySelector("#reader-prose");
const legendEl   = document.querySelector("#entity-legend");
const chapterList = document.querySelector("#chapter-list");
const prevButton  = document.querySelector("#prev-button");
const nextButton  = document.querySelector("#next-button");
const bookVizLink = document.querySelector("#book-viz-link");

// ── 完整实体类型定义（对齐 CLAUDE.md 规范）──
const ENTITY_LABELS = {
  concept:   { label: "核心概念", color: "var(--jade)" },
  identity:  { label: "身份稱謂", color: "#e8a87c" },
  person:    { label: "人物",     color: "var(--gold)" },
  deity:     { label: "神靈",     color: "#c890d4" },
  place:     { label: "地名",     color: "#7eb8da" },
  creature:  { label: "生物",     color: "#95c17b" },
  scripture: { label: "典籍",     color: "#4a9c7f" },
  school:    { label: "學派",     color: "#9b7fcf" },
  object:    { label: "器物",     color: "#e07040" },
  quantity:  { label: "數量",     color: "#aaaaaa" },
};

const BOOK_META = {
  daodejing: {
    label: "道德經",
    firstChapter: "001",
    vizHref: "../concept-map/",
    vizLabel: "概念星圖",
  },
  nanhua: {
    label: "南華真經",
    firstChapter: "01_逍遙遊",
    vizHref: "../fable-atlas/",
    vizLabel: "寓言圖鑑",
  },
};

const params       = new URLSearchParams(window.location.search);
const book         = BOOK_META[params.get("book")] ? params.get("book") : "daodejing";
const chapterParam = params.get("chapter") || (book === "daodejing" ? "001" : "01_逍遙遊");
const enabledTypes = new Set(Object.keys(ENTITY_LABELS));

let chaptersPayload = null;
let currentIndex    = 0;

// ── 渲染章节目录 ──
const renderChapterList = () => {
  chapterList.innerHTML = chaptersPayload.chapters
    .map((chapter, index) => {
      const active = index === currentIndex ? "active" : "";
      return `
        <button class="chapter-link ${active}" data-chapter="${chapter.id}">
          <span class="chapter-link-main">
            <strong>${chapter.title}</strong>
            <small>${book === "daodejing" ? chapter.id : chapter.section || ""}</small>
          </span>
          <span class="chapter-link-index">${chapter.number}</span>
        </button>
      `;
    })
    .join("");

  chapterList.querySelectorAll("[data-chapter]").forEach((button) => {
    button.addEventListener("click", () =>
      navigateTo("./", { book, chapter: button.dataset.chapter })
    );
  });

  const activeLink = chapterList.querySelector(".chapter-link.active");
  if (activeLink) activeLink.scrollIntoView({ block: "nearest", behavior: "smooth" });
};

// ── 渲染实体图例（右侧顶部，带颜色色块 + 点击筛选） ──
const renderLegend = () => {
  // 只显示当前章有实际出现的实体类型
  const presentTypes = new Set();
  if (chaptersPayload) {
    const chapter = chaptersPayload.chapters[currentIndex];
    for (const para of chapter.paragraphs || []) {
      for (const seg of para.segments || []) {
        if (seg.highlight && seg.entity_type) presentTypes.add(seg.entity_type);
      }
    }
  }

  legendEl.innerHTML = Object.entries(ENTITY_LABELS)
    .filter(([key]) => presentTypes.has(key))           // 只显示本章有的类型
    .map(([key, meta]) => {
      const active = enabledTypes.has(key) ? "active" : "";
      return `
        <button class="legend-tag ${active}" data-type="${key}" style="--tag-color:${meta.color}">
          <span class="legend-tag-dot"></span>
          <span>${meta.label}</span>
        </button>
      `;
    })
    .join("");

  legendEl.querySelectorAll(".legend-tag").forEach((btn) => {
    btn.addEventListener("click", () => {
      const type = btn.dataset.type;
      if (enabledTypes.has(type)) {
        enabledTypes.delete(type);
        btn.classList.remove("active");
      } else {
        enabledTypes.add(type);
        btn.classList.add("active");
      }
      renderProse();
    });
  });
};

// ── 只渲染正文（不重建图例/目录，避免闪烁） ──
const renderProse = () => {
  const chapter = chaptersPayload.chapters[currentIndex];
  proseEl.innerHTML = chapter.paragraphs
    .map((paragraph) => `
      <p id="pn-${paragraph.pn}">
        <a class="pn" data-pn="${paragraph.pn}">[${paragraph.pn}]</a>
        ${renderRichText(paragraph.segments, enabledTypes)}
      </p>
    `)
    .join("");

  proseEl.querySelectorAll(".pn").forEach((pnLink) => {
    pnLink.addEventListener("click", async () => {
      const chapter = chaptersPayload.chapters[currentIndex];
      const url = `${window.location.origin}${window.location.pathname}?book=${book}&chapter=${chapter.id}#pn-${pnLink.dataset.pn}`;
      await copyText(url);
      pnLink.textContent = `[${pnLink.dataset.pn}] ✓`;
      setTimeout(() => { pnLink.textContent = `[${pnLink.dataset.pn}]`; }, 1200);
    });
  });
};

// ── 渲染当前章节（完整） ──
const renderCurrentChapter = () => {
  const chapter = chaptersPayload.chapters[currentIndex];
  titleEl.textContent = `${chaptersPayload.metadata.title} · ${chapter.title}`;
  subtitleEl.textContent =
    `${chapter.number}/${chaptersPayload.chapters.length} · ${chapter.char_count} 字 · ${chapter.paragraphs.length} 段` +
    (chapter.section ? ` · ${chapter.section}` : "");

  renderProse();
  renderLegend();
  renderChapterList();

  prevButton.disabled = currentIndex === 0;
  nextButton.disabled = currentIndex === chaptersPayload.chapters.length - 1;

  document.title = `${chapter.title} — ${chaptersPayload.metadata.title}`;
  proseEl.scrollTop = 0;
  window.scrollTo({ top: 0, behavior: "smooth" });
};

const goToPrev = () => {
  if (currentIndex > 0)
    navigateTo("./", { book, chapter: chaptersPayload.chapters[currentIndex - 1].id });
};

const goToNext = () => {
  if (currentIndex < chaptersPayload.chapters.length - 1)
    navigateTo("./", { book, chapter: chaptersPayload.chapters[currentIndex + 1].id });
};

const bootstrapReader = async () => {
  chaptersPayload = await fetchJSON(`../data/${book}/chapters.json`);
  currentIndex = Math.max(
    0,
    chaptersPayload.chapters.findIndex((ch) => ch.id === chapterParam)
  );
  bookVizLink.href = BOOK_META[book].vizHref;
  bookVizLink.textContent = BOOK_META[book].vizLabel;
  renderCurrentChapter();

  prevButton.addEventListener("click", goToPrev);
  nextButton.addEventListener("click", goToNext);

  document.addEventListener("keydown", (e) => {
    if (["INPUT","TEXTAREA","SELECT"].includes(e.target.tagName)) return;
    if (e.key === "ArrowLeft")  { e.preventDefault(); goToPrev(); }
    if (e.key === "ArrowRight") { e.preventDefault(); goToNext(); }
  });
};

bootstrapReader();
