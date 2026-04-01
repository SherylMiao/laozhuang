const { createTooltip, fetchJSON, formatQuote, navigateTo } = window.DaozangShared;

const tooltipAtlas = createTooltip();
const atlasCanvas = document.querySelector("#atlas-canvas");
const atlasTitle = document.querySelector("#atlas-title");
const atlasDescriptionEl = document.querySelector("#atlas-description");
const atlasMeta = document.querySelector("#atlas-meta");
const atlasList = document.querySelector("#atlas-list");
const modeSelect = document.querySelector("#mode-select");
const sectionFilter = document.querySelector("#section-filter");
const themeLegend = document.querySelector("#theme-legend");
const fableSearch = document.querySelector("#fable-search");

let atlasData = null;
let currentMode = "fable";
let selectedNode = null;

// Theme color palette — map major theme categories to colors
const THEME_COLORS = {
  "養生": "rgba(148, 188, 123, 0.85)",
  "技藝與道": "rgba(91, 192, 190, 0.85)",
  "逍遙與有待": "rgba(126, 184, 218, 0.85)",
  "是非之辯": "rgba(180, 160, 220, 0.85)",
  "大小之辯": "rgba(180, 160, 220, 0.85)",
  "齊物": "rgba(180, 160, 220, 0.85)",
  "生死": "rgba(192, 90, 67, 0.75)",
  "處世": "rgba(201, 169, 110, 0.85)",
  "德充": "rgba(230, 190, 100, 0.85)",
  "治世批判": "rgba(220, 120, 120, 0.75)",
  "無用之用": "rgba(110, 180, 160, 0.85)",
  "天籟": "rgba(140, 200, 230, 0.85)",
};
const DEFAULT_FABLE_COLOR = "rgba(232, 168, 124, 0.85)";

const renderAtlasDetail = (item, mode) => {
  if (!item) {
    atlasTitle.textContent = "選擇寓言或人物";
    atlasDescriptionEl.innerHTML = `<p class="panel-copy">點擊圖中節點，即可查看人物出場、共享主題與原文入口。</p>`;
    atlasMeta.innerHTML = "";
    atlasList.innerHTML = '<div class="mini-card" style="color: var(--text-dim)">選擇節點後顯示</div>';
    return;
  }

  if (mode === "fable") {
    atlasTitle.textContent = item.name;

    // Truncated opening quote with expand toggle
    const quoteText = item.opening_quote || "";
    const truncLen = 120;
    const needsTrunc = quoteText.length > truncLen;
    atlasDescriptionEl.innerHTML = `
      <p class="opening-quote ${needsTrunc ? "truncated" : ""}" id="fable-quote">${quoteText}</p>
      ${needsTrunc ? '<button class="quote-toggle" id="quote-toggle">展開全文 ▾</button>' : ""}
    `;

    if (needsTrunc) {
      const toggleBtn = document.querySelector("#quote-toggle");
      const quoteEl = document.querySelector("#fable-quote");
      let expanded = false;
      toggleBtn.addEventListener("click", () => {
        expanded = !expanded;
        quoteEl.classList.toggle("truncated", !expanded);
        toggleBtn.textContent = expanded ? "收起 ▴" : "展開全文 ▾";
      });
    }

    atlasMeta.innerHTML = `
      <div class="pill"><span>篇目</span><strong>${item.chapter}</strong></div>
      <div class="pill"><span>段落</span><strong>${item.para_range}</strong></div>
      <div class="pill"><span>主題</span><strong>${item.themes.join(" / ") || "未標注"}</strong></div>
    `;
    atlasList.innerHTML = [
      ...item.characters.map((character) => `<div class="mini-card">${character}</div>`),
      `<button class="chapter-link" data-reader="${item.chapter}"><span>閱讀原文</span><span>→</span></button>`,
    ].join("");
  } else {
    atlasTitle.textContent = item.name;
    atlasDescriptionEl.innerHTML = `<p class="panel-copy">${item.description || "該角色暫無擴展說明。"}</p>`;
    atlasMeta.innerHTML = `
      <div class="pill"><span>出場寓言</span><strong>${item.fable_count}</strong></div>
      <div class="pill"><span>篇目</span><strong>${item.chapters.join(" / ")}</strong></div>
    `;
    atlasList.innerHTML = item.fable_ids
      .map((id) => {
        const fable = atlasData.fables.find((entry) => entry.id === id);
        if (!fable) return "";
        return `<button class="chapter-link" data-reader="${fable.chapter}"><span>${fable.name}</span><span>${fable.chapter}</span></button>`;
      })
      .join("");
  }

  document.querySelectorAll("[data-reader]").forEach((button) => {
    button.addEventListener("click", () => {
      navigateTo("../reader/", { book: "nanhua", chapter: button.dataset.reader });
    });
  });
};

const drawAtlas = () => {
  atlasCanvas.innerHTML = "";
  const width = atlasCanvas.clientWidth;
  const height = atlasCanvas.clientHeight;

  const svg = d3.select(atlasCanvas).append("svg")
    .attr("width", width)
    .attr("height", height);

  // Enable zoom/pan
  const g = svg.append("g");
  const zoom = d3.zoom()
    .scaleExtent([0.3, 4])
    .on("zoom", (event) => g.attr("transform", event.transform));
  svg.call(zoom);

  // Glow filter
  const defs = svg.append("defs");
  const filter = defs.append("filter").attr("id", "atlas-glow");
  filter.append("feGaussianBlur").attr("stdDeviation", 5).attr("result", "blur");
  const merge = filter.append("feMerge");
  merge.append("feMergeNode").attr("in", "blur");
  merge.append("feMergeNode").attr("in", "SourceGraphic");

  const sectionValue = sectionFilter.value;
  let nodes = [];
  let links = [];

  // sectionValue 有三种格式：
  // "all"          → 全部
  // "section:內篇"  → 按大分类（內篇/外篇/雜篇）
  // "01_逍遙遊"     → 具体单篇
  const matchSection = (item) => {
    if (sectionValue === "all") return true;
    if (sectionValue.startsWith("section:")) return item.section === sectionValue.slice(8);
    return item.chapter === sectionValue;
  };

  if (currentMode === "fable") {
    nodes = atlasData.fables
      .filter(matchSection)
      .map((item) => ({
        ...item,
        group: "fable",
        radius: Math.max(28, 22 + Math.sqrt(item.char_count) * 0.4),
      }));
    const visibleIds = new Set(nodes.map((item) => item.id));
    links = atlasData.links.filter(
      (item) => item.type === "主题关联" && visibleIds.has(item.source) && visibleIds.has(item.target),
    );
  } else {
    // 人物按篇筛选：看 character.chapters 是否包含目标篇目
    const matchCharSection = (item) => {
      if (sectionValue === "all") return true;
      const chs = item.chapters || [];
      if (sectionValue.startsWith("section:")) {
        const sec = sectionValue.slice(8);
        // 需要知道每章属于哪个 section，从 fable 数据推导
        const sectionOf = {};
        atlasData.fables.forEach((f) => { sectionOf[f.chapter] = f.section; });
        return chs.some((ch) => sectionOf[ch] === sec);
      }
      return chs.includes(sectionValue);
    };

    nodes = atlasData.characters
      .filter(matchCharSection)
      .map((item) => ({
        ...item,
        group: "character",
        radius: 18 + item.fable_count * 4,
      }));
    const visibleIds = new Set(nodes.map((item) => item.id));
    links = atlasData.links.filter(
      (item) => item.type === "辩论" && visibleIds.has(item.source) && visibleIds.has(item.target),
    );
  }

  const simulation = d3
    .forceSimulation(nodes.map((item) => ({ ...item })))
    .force("link", d3.forceLink(links.map((item) => ({ ...item }))).id((d) => d.id).distance(140))
    .force("charge", d3.forceManyBody().strength(-350))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius((d) => d.radius + 10))
    .force("x", d3.forceX(width / 2).strength(0.03))
    .force("y", d3.forceY(height / 2).strength(0.03));

  const link = g
    .append("g")
    .selectAll("line")
    .data(simulation.force("link").links())
    .join("line")
    .attr("stroke", (d) => d.type === "辩论" ? "rgba(192, 90, 67, 0.4)" : "rgba(255,255,255,0.12)")
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", (d) => d.type === "辩论" ? "6 4" : null);

  const fableColor = (d) => {
    if (!d.themes) return DEFAULT_FABLE_COLOR;
    for (const t of d.themes) {
      if (THEME_COLORS[t]) return THEME_COLORS[t];
    }
    return DEFAULT_FABLE_COLOR;
  };

  const node = g
    .append("g")
    .selectAll("g")
    .data(simulation.nodes())
    .join("g")
    .style("cursor", "pointer")
    .call(
      d3
        .drag()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }),
    );

  if (currentMode === "fable") {
    node
      .append("rect")
      .attr("x", (d) => -d.radius)
      .attr("y", -20)
      .attr("rx", 14)
      .attr("ry", 14)
      .attr("width", (d) => d.radius * 2)
      .attr("height", 40)
      .attr("fill", (d) => fableColor(d))
      .attr("fill-opacity", 0.8)
      .attr("stroke", (d) => selectedNode?.id === d.id ? "#f7ddb1" : "rgba(255,255,255,0.12)")
      .attr("stroke-width", (d) => selectedNode?.id === d.id ? 2.5 : 1)
      .attr("filter", (d) => selectedNode?.id === d.id ? "url(#atlas-glow)" : null);
  } else {
    node
      .append("circle")
      .attr("r", (d) => d.radius)
      .attr("fill", "rgba(201, 169, 110, 0.75)")
      .attr("fill-opacity", 0.8)
      .attr("stroke", (d) => selectedNode?.id === d.id ? "#f7ddb1" : "rgba(255,255,255,0.15)")
      .attr("stroke-width", (d) => selectedNode?.id === d.id ? 2.5 : 1)
      .attr("filter", (d) => selectedNode?.id === d.id ? "url(#atlas-glow)" : null);
  }

  node
    .append("text")
    .text((d) => d.name.length > 6 ? d.name.slice(0, 5) + "…" : d.name)
    .attr("text-anchor", "middle")
    .attr("dy", 5)
    .attr("fill", currentMode === "fable" ? "#10141b" : "#f5efe2")
    .attr("font-size", 12)
    .attr("font-weight", 600)
    .attr("pointer-events", "none");

  node
    .on("mouseenter", (event, d) => {
      const shape = d3.select(event.currentTarget).select(currentMode === "fable" ? "rect" : "circle");
      shape.transition().duration(150)
        .attr("fill-opacity", 1)
        .attr("stroke-width", 2);
      tooltipAtlas.show(
        `<strong>${d.name}</strong><br />${currentMode === "fable" ? `${d.themes.join(" / ")}<br /><span style="opacity:.7">${formatQuote(d.opening_quote, 80)}</span>` : `${d.fable_count} 則寓言`}`,
        event.clientX,
        event.clientY,
      );
    })
    .on("mousemove", (event) => tooltipAtlas.move(event.clientX, event.clientY))
    .on("mouseleave", (event) => {
      const d = d3.select(event.currentTarget).datum();
      const shape = d3.select(event.currentTarget).select(currentMode === "fable" ? "rect" : "circle");
      shape.transition().duration(200)
        .attr("fill-opacity", 0.8)
        .attr("stroke-width", selectedNode?.id === d.id ? 2.5 : 1);
      tooltipAtlas.hide();
    })
    .on("click", (_, d) => {
      selectedNode = d;
      renderAtlasDetail(d, currentMode);
      drawAtlas();
    });

  simulation.on("tick", () => {
    link
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x)
      .attr("y2", (d) => d.target.y);
    node.attr("transform", (d) => `translate(${d.x}, ${d.y})`);
  });
};

const bootstrapAtlas = async () => {
  atlasData = await fetchJSON("../data/nanhua/fable_graph.json");

  // Build unique theme set for legend
  const themeSet = new Map();
  atlasData.fables.forEach((f) => {
    f.themes.forEach((t) => themeSet.set(t, (themeSet.get(t) || 0) + 1));
  });

  // Show top themes (2+ fables) + an "其他" chip
  const sorted = Array.from(themeSet.entries()).sort((a, b) => b[1] - a[1]);
  const TOP_THRESHOLD = 2;
  const topThemes = sorted.filter(([, c]) => c >= TOP_THRESHOLD);
  const otherCount = sorted.filter(([, c]) => c < TOP_THRESHOLD).reduce((s, [, c]) => s + c, 0);

  themeLegend.innerHTML = topThemes
    .map(([name, count]) => {
      const col = THEME_COLORS[name] || DEFAULT_FABLE_COLOR;
      return `<span class="legend-chip" style="--chip-color:${col}">${name} · ${count}</span>`;
    })
    .join("")
    + (otherCount > 0 ? `<span class="legend-chip" style="--chip-color:${DEFAULT_FABLE_COLOR}">其他 · ${otherCount}</span>` : "");

  modeSelect.addEventListener("change", () => {
    currentMode = modeSelect.value;
    selectedNode = null;
    renderAtlasDetail(null, currentMode);
    drawAtlas();
  });
  sectionFilter.addEventListener("change", drawAtlas);

  // Search functionality
  fableSearch.addEventListener("input", () => {
    const value = fableSearch.value.trim();
    if (!value) return;
    const pool = currentMode === "fable" ? atlasData.fables : atlasData.characters;
    const matched = pool.find((item) => item.name.includes(value));
    if (matched) {
      selectedNode = matched;
      renderAtlasDetail(matched, currentMode);
      drawAtlas();
    }
  });

  selectedNode = atlasData.fables[0];
  renderAtlasDetail(selectedNode, currentMode);
  drawAtlas();
  window.addEventListener("resize", drawAtlas);
};

bootstrapAtlas();
