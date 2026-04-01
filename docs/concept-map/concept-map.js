const { createTooltip, fetchJSON, formatQuote, navigateTo } = window.DaozangShared;

const tooltip        = createTooltip();
const canvas         = document.querySelector("#concept-canvas");
const detailTitle    = document.querySelector("#detail-title");
const detailDescription = document.querySelector("#detail-description");
const detailMeta     = document.querySelector("#detail-meta");
const quoteList      = document.querySelector("#quote-list");
const chapterList    = document.querySelector("#chapter-list");
const categoryFilter = document.querySelector("#category-filter");
const searchInput    = document.querySelector("#search-input");
const categoryLegend = document.querySelector("#category-legend");

let graphData      = null;
let currentCategory = "all";
let selectedId     = null;

// ── 右侧详情面板（不触发图重建）──
const renderDetail = (node) => {
  if (!node) {
    detailTitle.textContent = "選擇一個概念";
    detailDescription.textContent = "點擊星圖中的節點，即可查看概念的分類、出現頻次、關聯章節與關鍵引文。";
    detailMeta.innerHTML = "";
    quoteList.innerHTML  = '<div class="mini-card" style="color: var(--text-dim)">選擇概念後顯示</div>';
    chapterList.innerHTML = '<div class="mini-card" style="color: var(--text-dim)">選擇概念後顯示</div>';
    return;
  }

  detailTitle.textContent = node.name;
  detailDescription.textContent = node.description || "暫無補充說明。";
  detailMeta.innerHTML = `
    <div class="pill"><span>分類</span><strong>${node.category}</strong></div>
    <div class="pill"><span>頻次</span><strong>${node.frequency}</strong></div>
    <div class="pill"><span>章節</span><strong>${node.chapters.length}</strong></div>
  `;

  quoteList.innerHTML = node.key_quotes.length
    ? node.key_quotes.map((q) => `
        <button class="quote-card" data-chapter="${String(q.chapter).padStart(3, "0")}">
          <strong>第 ${q.chapter} 章</strong>
          <div>${formatQuote(q.text, 120)}</div>
        </button>
      `).join("")
    : '<div class="mini-card" style="color: var(--text-dim)">暫無引文</div>';

  chapterList.innerHTML = node.chapters.length
    ? `<div style="display:flex;flex-wrap:wrap;gap:6px">${node.chapters.map((ch) => `
        <button class="pill" data-chapter="${String(ch).padStart(3, "0")}"
          style="cursor:pointer;border:1px solid rgba(255,255,255,0.08)">
          <span>第 ${ch} 章</span>
        </button>
      `).join("")}</div>`
    : '<div class="mini-card" style="color: var(--text-dim)">暫無章節</div>';

  document.querySelectorAll("[data-chapter]").forEach((btn) => {
    btn.addEventListener("click", () =>
      navigateTo("../reader/", { book: "daodejing", chapter: btn.dataset.chapter })
    );
  });
};

// ── 节点半径（对数压缩）──
const nodeRadius = (d) => 10 + Math.log1p(d.frequency) * 3.2;

// ── 就地更新节点高亮（不销毁 SVG）──
let updateHighlight = null;

// ── 绘图主函数（只在 category 切换或 resize 时调用）──
const drawGraph = () => {
  canvas.innerHTML = "";
  const width  = canvas.clientWidth;
  const height = canvas.clientHeight;

  const svg = d3.select(canvas).append("svg")
    .attr("width", width)
    .attr("height", height)
    .style("opacity", 0); // 稳定后再 fade in

  const g = svg.append("g");

  // zoom / pan
  const zoom = d3.zoom()
    .scaleExtent([0.3, 4])
    .on("zoom", (event) => g.attr("transform", event.transform));
  svg.call(zoom);

  // glow filter
  const defs = svg.append("defs");
  const glowFilter = defs.append("filter").attr("id", "node-glow");
  glowFilter.append("feGaussianBlur").attr("stdDeviation", 4).attr("result", "blur");
  const merge = glowFilter.append("feMerge");
  merge.append("feMergeNode").attr("in", "blur");
  merge.append("feMergeNode").attr("in", "SourceGraphic");

  const visibleNodes = graphData.nodes.filter(
    (n) => currentCategory === "all" || n.category === currentCategory
  );
  const visibleIds  = new Set(visibleNodes.map((n) => n.id));
  const visibleLinks = graphData.links.filter(
    (l) => visibleIds.has(l.source) && visibleIds.has(l.target)
  );

  const color = (cat) => graphData.categories[cat]?.color || "#5bc0be";

  // ── Force simulation ──
  // 先预热 300 tick，稳定后一次性渲染，避免初始"动画乱跑"
  const simNodes = visibleNodes.map((n) => ({ ...n }));
  const simLinks = visibleLinks.map((l) => ({ ...l }));

  const simulation = d3.forceSimulation(simNodes)
    .force("link", d3.forceLink(simLinks)
      .id((d) => d.id)
      .distance((d) => {
        const wMax = 27;
        return 70 + (1 - Math.min(d.weight, wMax) / wMax) * 60;
      })
      .strength((d) => 0.3 + Math.min(d.weight, 10) / 10 * 0.4)
    )
    .force("charge", d3.forceManyBody()
      .strength((d) => -500 - Math.log1p(d.frequency) * 40)
      .distanceMin(8)
      .distanceMax(400)
    )
    .force("center", d3.forceCenter(width / 2, height / 2).strength(0.1))
    .force("collision", d3.forceCollide().radius((d) => nodeRadius(d) + 6).strength(0.85))
    .force("x", d3.forceX(width / 2).strength(0.07))
    .force("y", d3.forceY(height / 2).strength(0.07))
    .stop(); // 先不跑 tick loop

  // 预热：同步跑 300 次 tick
  const warmupTicks = Math.ceil(Math.log(simulation.alphaMin()) / Math.log(1 - simulation.alphaDecay()));
  for (let i = 0; i < Math.min(warmupTicks, 300); i++) simulation.tick();

  // ── 渲染边 ──
  const link = g.append("g")
    .attr("stroke-linecap", "round")
    .selectAll("line")
    .data(simulation.force("link").links())
    .join("line")
    .attr("stroke", (d) =>
      d.type === "对立" ? "rgba(192,90,67,0.5)"
      : d.type === "蕴含" ? "rgba(91,192,190,0.35)"
      : "rgba(255,255,255,0.1)"
    )
    .attr("stroke-width", (d) => Math.max(1, d.weight * 0.28))
    .attr("stroke-dasharray", (d) => d.type === "对立" ? "4 4" : null)
    .attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y)
    .attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);

  // ── 渲染节点 ──
  const node = g.append("g")
    .selectAll("g")
    .data(simulation.nodes())
    .join("g")
    .style("cursor", "pointer")
    .attr("transform", (d) => `translate(${d.x},${d.y})`)
    .call(d3.drag()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.15).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on("end",  (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null; d.fy = null;
      })
    );

  const circle = node.append("circle")
    .attr("r", nodeRadius)
    .attr("fill", (d) => color(d.category))
    .attr("fill-opacity", 0.72)
    .attr("stroke", (d) => d.id === selectedId ? "#f6ddad" : color(d.category))
    .attr("stroke-width", (d) => d.id === selectedId ? 2.5 : 1.2)
    .attr("stroke-opacity", (d) => d.id === selectedId ? 1 : 0.35)
    .attr("filter", (d) => d.id === selectedId ? "url(#node-glow)" : null);

  node.append("text")
    .text((d) => d.name)
    .attr("text-anchor", "middle")
    .attr("dy", 5)
    .attr("fill", "#f5efe2")
    .attr("font-size", (d) => Math.max(10, 9 + Math.log1p(d.frequency) * 0.9))
    .attr("font-weight", 500)
    .attr("pointer-events", "none");

  // ── 就地高亮更新（不重建 SVG）──
  updateHighlight = () => {
    circle
      .attr("stroke", (d) => d.id === selectedId ? "#f6ddad" : color(d.category))
      .attr("stroke-width", (d) => d.id === selectedId ? 2.5 : 1.2)
      .attr("stroke-opacity", (d) => d.id === selectedId ? 1 : 0.35)
      .attr("filter", (d) => d.id === selectedId ? "url(#node-glow)" : null);

    // 连接线：选中节点的边高亮
    link
      .attr("stroke-opacity", (d) =>
        d.source.id === selectedId || d.target.id === selectedId ? 0.7 : 0.2
      )
      .attr("stroke-width", (d) =>
        d.source.id === selectedId || d.target.id === selectedId
          ? Math.max(1.5, d.weight * 0.4)
          : Math.max(0.8, d.weight * 0.2)
      );
  };
  updateHighlight();

  // ── 交互：hover / click ──
  node
    .on("mouseenter", (event, d) => {
      d3.select(event.currentTarget).select("circle")
        .transition().duration(150)
        .attr("r", nodeRadius(d) * 1.12)
        .attr("fill-opacity", 1)
        .attr("stroke-opacity", 0.8);
      tooltip.show(
        `<strong>${d.name}</strong><br /><span style="opacity:.7">${d.category} · ${d.frequency} 次</span><br />${formatQuote(d.key_quotes[0]?.text || d.description || "", 80)}`,
        event.clientX, event.clientY
      );
    })
    .on("mousemove", (event) => tooltip.move(event.clientX, event.clientY))
    .on("mouseleave", (event) => {
      const d = d3.select(event.currentTarget).datum();
      d3.select(event.currentTarget).select("circle")
        .transition().duration(200)
        .attr("r", nodeRadius(d))
        .attr("fill-opacity", 0.72)
        .attr("stroke-opacity", d.id === selectedId ? 1 : 0.35);
      tooltip.hide();
    })
    .on("click", (_, d) => {
      // 只更新 selectedId + 详情面板 + 高亮，不重建 SVG
      selectedId = d.id;
      renderDetail(d);
      updateHighlight();
    });

  // drag 时继续 tick
  simulation.on("tick", () => {
    link
      .attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
    node.attr("transform", (d) => `translate(${d.x},${d.y})`);
  });

  // ── fit view + fade in ──
  const bounds = g.node().getBBox();
  if (bounds.width && bounds.height) {
    const scale = Math.min(
      width  / (bounds.width  + 80),
      height / (bounds.height + 80)
    ) * 1.5;
    const tx = width  / 2 - (bounds.x + bounds.width  / 2) * scale;
    const ty = height / 2 - (bounds.y + bounds.height / 2) * scale;
    svg.call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
  }

  svg.transition().duration(400).style("opacity", 1);
};

// ── 启动 ──
const bootstrap = async () => {
  graphData = await fetchJSON("../data/daodejing/concept_graph.json");

  // category filter 下拉
  Object.keys(graphData.categories).forEach((cat) => {
    const opt = document.createElement("option");
    opt.value = cat; opt.textContent = cat;
    categoryFilter.appendChild(opt);
  });

  // category legend chips
  categoryLegend.innerHTML = Object.entries(graphData.categories)
    .map(([name, payload]) =>
      `<span class="legend-chip" style="--chip-color:${payload.color}">${name} · ${payload.concepts.length}</span>`
    ).join("");

  categoryFilter.addEventListener("change", () => {
    currentCategory = categoryFilter.value;
    drawGraph();
  });

  searchInput.addEventListener("input", () => {
    const val = searchInput.value.trim();
    if (!val) return;
    const matched = graphData.nodes.find((n) => n.name.includes(val));
    if (matched) {
      selectedId = matched.id;
      renderDetail(matched);
      // 若节点在当前可见集里就直接更新高亮，否则重绘
      if (updateHighlight) updateHighlight();
      else drawGraph();
    }
  });

  // 默认选中第一个节点
  selectedId = graphData.nodes[0].id;
  renderDetail(graphData.nodes[0]);
  drawGraph();

  window.addEventListener("resize", drawGraph);
};

bootstrap();
