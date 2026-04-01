window.DaozangShared = (() => {
  const escapeHtml = (value) =>
    String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");

  const fetchJSON = async (path) => {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`加载失败: ${path}`);
    }
    return response.json();
  };

  const formatQuote = (text, maxLen = 88) => {
    if (!text) return "";
    return text.length <= maxLen ? text : `${text.slice(0, maxLen)}…`;
  };

  const navigateTo = (page, params = {}) => {
    const url = new URL(page, window.location.href);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, value);
      }
    });
    window.location.href = url.toString();
  };

  const createTooltip = () => {
    let tooltip = document.querySelector(".tooltip");
    if (!tooltip) {
      tooltip = document.createElement("div");
      tooltip.className = "tooltip";
      document.body.appendChild(tooltip);
    }
    return {
      show(content, x, y) {
        tooltip.innerHTML = content;
        tooltip.style.left = `${x + 18}px`;
        tooltip.style.top = `${y + 18}px`;
        tooltip.classList.add("visible");
      },
      move(x, y) {
        tooltip.style.left = `${x + 18}px`;
        tooltip.style.top = `${y + 18}px`;
      },
      hide() {
        tooltip.classList.remove("visible");
      },
    };
  };

  const renderRichText = (segments, enabledTypes = null) =>
    segments
      .map((segment) => {
        const text = escapeHtml(segment.text);
        if (!segment.highlight) return text;
        const type = segment.entity_type;
        const hidden = enabledTypes && !enabledTypes.has(type);
        return `<span class="entity entity-${type}${hidden ? " hidden" : ""}" data-entity-type="${type}" data-canonical="${escapeHtml(segment.canonical || segment.text)}">${text}</span>`;
      })
      .join("");

  const highlightEntities = (text, entities = []) => {
    if (!entities.length) return escapeHtml(text);
    let rendered = escapeHtml(text);
    entities.forEach((entity) => {
      rendered = rendered.replace(
        escapeHtml(entity.display),
        `<span class="entity entity-${entity.type}" data-entity-type="${entity.type}">${escapeHtml(entity.display)}</span>`,
      );
    });
    return rendered;
  };

  const copyText = async (value) => {
    await navigator.clipboard.writeText(value);
  };

  return {
    copyText,
    createTooltip,
    escapeHtml,
    fetchJSON,
    formatQuote,
    highlightEntities,
    navigateTo,
    renderRichText,
  };
})();
