const COLORS = {
  "Outstanding Winner": "#b04632",
  Finalist: "#d39b22",
  "Meritorious Winner": "#126a5a",
  "Honorable Mention": "#315d9d",
  "Successful Participant": "#6f7b8c",
  "Unsuccessful Participant": "#8a5a9e",
  Disqualified: "#202a36",
  "Not Judged": "#9aa4b2",
};

const CODES = {
  "Outstanding Winner": "O",
  Finalist: "F",
  "Meritorious Winner": "M",
  "Honorable Mention": "H",
  "Successful Participant": "S",
  "Unsuccessful Participant": "U",
  Disqualified: "D",
  "Not Judged": "N",
};

const LABELS_CN = {
  "Outstanding Winner": "Outstanding Winner",
  Finalist: "Finalist",
  "Meritorious Winner": "Meritorious Winner",
  "Honorable Mention": "Honorable Mention",
  "Successful Participant": "Successful Participant",
  "Unsuccessful Participant": "Unsuccessful Participant",
  Disqualified: "Disqualified",
  "Not Judged": "Not Judged",
};

const AWARD_CN = {
  "Outstanding Winner": "O 奖",
  Finalist: "F 奖",
  "Meritorious Winner": "M 奖",
  "Honorable Mention": "H 奖",
  "Successful Participant": "S 奖",
  "Unsuccessful Participant": "U 奖",
  Disqualified: "D",
  "Not Judged": "N",
};

const HIGH_AWARDS = new Set(["Outstanding Winner", "Finalist", "Meritorious Winner", "Honorable Mention"]);

const state = {
  records: [],
  summary: null,
  institutions: [],
  globalInstitutionStats: new Map(),
  selectedInstitution: "",
  selectedInstitutionKey: "",
  selectedRows: [],
};

const $ = (id) => document.getElementById(id);
const fmt = new Intl.NumberFormat("en-US");

function countBy(rows, key) {
  return rows.reduce((acc, row) => {
    const value = row[key] || "Unknown";
    acc[value] = (acc[value] || 0) + 1;
    return acc;
  }, {});
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function specificAward(row) {
  const base = `${AWARD_CN[row.designation] || row.designation} · ${row.designation}`;
  if (!row.special_award || row.special_award === "-") return base;
  return `${base} · ${row.special_award}`;
}

function institutionGroupFor(row) {
  return state.institutions.find((item) => item.key === normalize(row.institution));
}

function displayCn(row) {
  return row.institution_cn || institutionGroupFor(row)?.cn || "-";
}

function displayInstitution(row) {
  const group = institutionGroupFor(row);
  const canonical = group?.name || row.institution || "Unknown institution";
  const raw = row.institution_raw || row.institution || "";
  if (!raw || normalize(raw) === normalize(canonical)) return escapeHtml(canonical);
  return `
    <strong>${escapeHtml(canonical)}</strong>
    <span class="source-name">PDF: ${escapeHtml(raw)}</span>
  `;
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function compactSearch(value) {
  return normalize(value).replace(/\s+/g, "");
}

function displayPercent(value) {
  if (!Number.isFinite(value)) return "0%";
  return `${Math.round(value * 10) / 10}%`;
}

function setupFilters() {
  const designationFilter = $("designationFilter");
  state.summary.designation_order.forEach((designation) => {
    const option = document.createElement("option");
    option.value = designation;
    option.textContent = `${CODES[designation]} · ${designation}`;
    designationFilter.appendChild(option);
  });

  const problemFilter = $("problemFilter");
  state.summary.problem_order.forEach((problem) => {
    const option = document.createElement("option");
    option.value = problem;
    option.textContent = `Problem ${problem}`;
    problemFilter.appendChild(option);
  });

  designationFilter.addEventListener("change", renderTable);
  problemFilter.addEventListener("change", renderTable);
}

function buildInstitutionIndex() {
  const groups = new Map();
  state.records.forEach((row) => {
    if (!row.institution) return;
    const key = normalize(row.institution);
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        count: 0,
        highAwardCount: 0,
        variants: new Map(),
        cnVariants: new Map(),
        teams: new Set(),
        problems: new Set(),
      });
    }
    const group = groups.get(key);
    group.count += 1;
    if (HIGH_AWARDS.has(row.designation)) group.highAwardCount += 1;
    group.variants.set(row.institution, (group.variants.get(row.institution) || 0) + 1);
    if (row.institution_cn) group.cnVariants.set(row.institution_cn, (group.cnVariants.get(row.institution_cn) || 0) + 1);
    group.teams.add(row.team);
    group.problems.add(row.problem);
  });

  state.institutions = [...groups.values()]
    .map((group) => {
      const variants = [...group.variants.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
      const cnVariants = [...group.cnVariants.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
      const cn = cnVariants[0]?.[0] || "";
      const tokens = [group.key, compactSearch(group.key), cn, compactSearch(cn), ...variants.map(([name]) => name)];
      return {
        ...group,
        cn,
        searchText: tokens.filter(Boolean).join(" ").toLowerCase(),
        name: variants[0][0],
        variantNames: variants.map(([name]) => name),
      };
    })
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));

  state.globalInstitutionStats = new Map(state.institutions.map((item, index) => [item.key, { ...item, rank: index + 1 }]));

  $("schoolSuggestions").innerHTML = state.institutions
    .slice(0, 700)
    .flatMap((item) => [item.name, item.cn].filter(Boolean))
    .map((name) => `<option value="${escapeHtml(name)}"></option>`)
    .join("");
}

function renderSummaryCards() {
  const summary = state.summary;
  const expectedTotal = Object.values(summary.expected).reduce((sum, problem) => {
    return sum + Object.values(problem).reduce((inner, value) => inner + value, 0);
  }, 0);

  const cards = [
    ["抽取名单", fmt.format(summary.record_count), "PDF 逐行获奖名单记录"],
    ["学校名", fmt.format(summary.institution_count), "按 PDF 中英文学校名聚合"],
    ["中文名", fmt.format(Object.keys(summary.institution_names_cn || {}).length), "已建立中文搜索映射"],
    ["官方总数", fmt.format(expectedTotal), "来自每份 PDF 首页摘要"],
    ["题目", "A-F", "MCM A-C / ICM D-F"],
  ];

  $("summaryCards").innerHTML = cards
    .map(
      ([label, value, hint]) => `
        <div class="metric-card">
          <div class="metric-value">${value}</div>
          <div class="metric-label">${label} · ${hint}</div>
        </div>
      `,
    )
    .join("");

  $("dataNote").textContent =
    "注：Problem A 的官方首页摘要为 8,574 队，逐行名单抽取为 8,575 队；中文校名映射优先覆盖高频学校和常见长校名，未确认的学校不强行翻译。";
}

function getMatches(query) {
  const q = normalize(query);
  const compact = compactSearch(query);
  if (!q) return state.institutions.slice(0, 8);

  const teamHit = state.records.find((row) => row.team === q);
  if (teamHit?.institution) {
    const group = state.institutions.find((item) => item.key === normalize(teamHit.institution));
    if (group) return [group];
  }

  const starts = [];
  const contains = [];
  state.institutions.forEach((item) => {
    const startsCn = item.cn && (normalize(item.cn).startsWith(q) || compactSearch(item.cn).startsWith(compact));
    if (item.key.startsWith(q) || startsCn) starts.push(item);
    else if (item.searchText.includes(q) || (compact && item.searchText.includes(compact))) contains.push(item);
  });
  return [...starts, ...contains].slice(0, 10);
}

function renderMatches(query) {
  const matches = getMatches(query);
  $("matchList").innerHTML = matches
    .map(
      (item) => `
        <button class="match-button ${item.key === state.selectedInstitutionKey ? "active" : ""}"
          type="button" data-school-key="${escapeHtml(item.key)}">
          <span class="match-name">${escapeHtml(item.name)}${item.cn ? `<span class="match-cn">${escapeHtml(item.cn)}</span>` : ""}</span>
          <span class="match-count">${fmt.format(item.count)} teams</span>
        </button>
      `,
    )
    .join("");

  document.querySelectorAll(".match-button").forEach((button) => {
    button.addEventListener("click", () => selectInstitution(button.dataset.schoolKey));
  });
}

function selectInstitution(key) {
  const item = state.institutions.find((institution) => institution.key === key);
  state.selectedInstitution = item?.name || "";
  state.selectedInstitutionKey = item?.key || "";
  $("schoolSearch").value = state.selectedInstitution;
  state.selectedRows = state.records
    .filter((row) => normalize(row.institution) === state.selectedInstitutionKey)
    .sort((a, b) => a.problem.localeCompare(b.problem) || a.team.localeCompare(b.team));

  $("schoolTitle").textContent = state.selectedInstitution || "请选择一个学校";
  $("schoolCnTitle").textContent = item?.cn || "";
  $("schoolTotal").textContent = `${fmt.format(state.selectedRows.length)} teams`;
  $("designationFilter").value = "";
  $("problemFilter").value = "";

  renderMatches(state.selectedInstitution);
  renderAwardChips();
  renderSchoolCharts();
  renderSchoolAnalysis();
  renderTable();
}

function renderAwardChips() {
  const counts = countBy(state.selectedRows, "designation");
  $("awardChips").innerHTML = state.summary.designation_order
    .map((designation) => {
      const count = counts[designation] || 0;
      return `
        <div class="award-chip" style="--chip-color:${COLORS[designation]}">
          <div class="chip-code">${CODES[designation]}</div>
          <div class="chip-count">${fmt.format(count)}</div>
          <div class="chip-label">${LABELS_CN[designation]}</div>
        </div>
      `;
    })
    .join("");
}

function drawEmpty(canvas, message) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#f7f8fb";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#647084";
  ctx.font = "16px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(message, canvas.width / 2, canvas.height / 2);
}

function drawBarChart(canvas, items, options = {}) {
  const ctx = canvas.getContext("2d");
  const padding = options.padding || { top: 28, right: 24, bottom: 66, left: 58 };
  const width = canvas.width;
  const height = canvas.height;
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;
  const max = Math.max(1, ...items.map((item) => item.value));

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "#dce2ea";
  ctx.lineWidth = 1;

  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + chartH - (chartH * i) / 4;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
    ctx.fillStyle = "#647084";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "right";
    ctx.fillText(Math.round((max * i) / 4), padding.left - 8, y + 4);
  }

  const gap = options.gap || 12;
  const barW = Math.max(16, (chartW - gap * (items.length - 1)) / Math.max(1, items.length));
  items.forEach((item, index) => {
    const x = padding.left + index * (barW + gap);
    const barH = (item.value / max) * chartH;
    const y = padding.top + chartH - barH;

    ctx.fillStyle = item.color || "#126a5a";
    ctx.fillRect(x, y, barW, barH);
    ctx.fillStyle = "#18202f";
    ctx.font = "bold 13px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(String(item.value), x + barW / 2, y - 7);

    ctx.save();
    ctx.translate(x + barW / 2, height - padding.bottom + 20);
    ctx.rotate(options.rotateLabels ? -Math.PI / 5 : 0);
    ctx.fillStyle = "#647084";
    ctx.font = "12px sans-serif";
    ctx.textAlign = options.rotateLabels ? "right" : "center";
    ctx.fillText(item.label, 0, 0);
    ctx.restore();
  });
}

function drawHorizontalBarChart(canvas, items) {
  const ctx = canvas.getContext("2d");
  const padding = { top: 20, right: 46, bottom: 24, left: 222 };
  const width = canvas.width;
  const height = canvas.height;
  const rowH = (height - padding.top - padding.bottom) / Math.max(1, items.length);
  const max = Math.max(1, ...items.map((item) => item.value));

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);

  items.forEach((item, index) => {
    const y = padding.top + index * rowH + rowH * 0.2;
    const barH = Math.max(8, rowH * 0.55);
    const barW = ((width - padding.left - padding.right) * item.value) / max;

    ctx.fillStyle = "#647084";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "right";
    const label = item.label.length > 30 ? `${item.label.slice(0, 29)}...` : item.label;
    ctx.fillText(label, padding.left - 12, y + barH * 0.72);

    ctx.fillStyle = index % 3 === 0 ? "#126a5a" : index % 3 === 1 ? "#315d9d" : "#b04632";
    ctx.fillRect(padding.left, y, barW, barH);
    ctx.fillStyle = "#18202f";
    ctx.font = "bold 12px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(fmt.format(item.value), padding.left + barW + 8, y + barH * 0.72);
  });
}

function renderSchoolCharts() {
  const awardCanvas = $("awardChart");
  const problemCanvas = $("problemChart");

  if (!state.selectedRows.length) {
    drawEmpty(awardCanvas, "请选择学校");
    drawEmpty(problemCanvas, "请选择学校");
    drawEmpty($("heatmapChart"), "请选择学校");
    return;
  }

  const awardCounts = countBy(state.selectedRows, "designation");
  const awardItems = state.summary.designation_order.map((designation) => ({
    label: CODES[designation],
    value: awardCounts[designation] || 0,
    color: COLORS[designation],
  }));
  drawBarChart(awardCanvas, awardItems);

  const problemCounts = countBy(state.selectedRows, "problem");
  const problemItems = state.summary.problem_order.map((problem) => ({
    label: `P${problem}`,
    value: problemCounts[problem] || 0,
    color: problem <= "C" ? "#315d9d" : "#126a5a",
  }));
  drawBarChart(problemCanvas, problemItems, { padding: { top: 28, right: 24, bottom: 52, left: 58 } });
  drawHeatmap($("heatmapChart"), state.selectedRows);
}

function renderTopChart() {
  const items = state.summary.top_institutions.slice(0, 20).map(([label, value]) => ({ label, value }));
  drawHorizontalBarChart($("topChart"), items);

  const highItems = [...state.globalInstitutionStats.values()]
    .filter((item) => item.highAwardCount > 0)
    .sort((a, b) => b.highAwardCount - a.highAwardCount || b.count - a.count)
    .slice(0, 20)
    .map((item) => ({ label: item.cn ? `${item.name} / ${item.cn}` : item.name, value: item.highAwardCount }));
  drawHorizontalBarChart($("topHighAwardChart"), highItems);
}

function drawHeatmap(canvas, rows) {
  const ctx = canvas.getContext("2d");
  const problems = state.summary.problem_order;
  const designations = state.summary.designation_order;
  const counts = {};
  rows.forEach((row) => {
    const key = `${row.problem}|${row.designation}`;
    counts[key] = (counts[key] || 0) + 1;
  });
  const max = Math.max(1, ...Object.values(counts));
  const width = canvas.width;
  const height = canvas.height;
  const padding = { top: 42, right: 24, bottom: 38, left: 150 };
  const cellW = (width - padding.left - padding.right) / designations.length;
  const cellH = (height - padding.top - padding.bottom) / problems.length;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, width, height);
  ctx.font = "12px sans-serif";
  ctx.textAlign = "center";
  designations.forEach((designation, index) => {
    ctx.fillStyle = "#647084";
    ctx.fillText(CODES[designation], padding.left + index * cellW + cellW / 2, 24);
  });
  problems.forEach((problem, rowIndex) => {
    ctx.fillStyle = "#647084";
    ctx.textAlign = "right";
    ctx.fillText(`Problem ${problem}`, padding.left - 12, padding.top + rowIndex * cellH + cellH / 2 + 4);
    designations.forEach((designation, colIndex) => {
      const value = counts[`${problem}|${designation}`] || 0;
      const strength = value / max;
      const x = padding.left + colIndex * cellW;
      const y = padding.top + rowIndex * cellH;
      ctx.fillStyle = value ? `rgba(18, 106, 90, ${0.18 + strength * 0.72})` : "#f4f6f9";
      ctx.fillRect(x + 3, y + 3, cellW - 6, cellH - 6);
      ctx.strokeStyle = "#dce2ea";
      ctx.strokeRect(x + 3, y + 3, cellW - 6, cellH - 6);
      ctx.fillStyle = strength > 0.58 ? "#fff" : "#18202f";
      ctx.textAlign = "center";
      ctx.font = "bold 13px sans-serif";
      ctx.fillText(String(value), x + cellW / 2, y + cellH / 2 + 5);
    });
  });
}

function renderSchoolAnalysis() {
  if (!state.selectedRows.length) {
    $("schoolAnalysis").innerHTML = `<div class="analysis-card"><div class="analysis-label">请选择学校查看排名、奖项率和题目覆盖。</div></div>`;
    return;
  }
  const stat = state.globalInstitutionStats.get(state.selectedInstitutionKey);
  const total = state.selectedRows.length;
  const high = state.selectedRows.filter((row) => HIGH_AWARDS.has(row.designation)).length;
  const outstanding = state.selectedRows.filter((row) => row.designation === "Outstanding Winner").length;
  const finalist = state.selectedRows.filter((row) => row.designation === "Finalist").length;
  const problems = new Set(state.selectedRows.map((row) => row.problem)).size;
  const countries = new Set(state.selectedRows.map((row) => row.country).filter(Boolean)).size;
  const cards = [
    [`#${stat?.rank || "-"}`, "学校总队伍数排名"],
    [fmt.format(high), `高奖项队伍 O/F/M/H，占 ${displayPercent((high / total) * 100)}`],
    [fmt.format(outstanding + finalist), "Outstanding + Finalist"],
    [`${problems}/6`, "覆盖题目数量"],
    [fmt.format(countries), "国家/地区来源"],
    [fmt.format(total), "该校总队伍数"],
  ];
  $("schoolAnalysis").innerHTML = cards
    .map(([value, label]) => `<div class="analysis-card"><div class="analysis-value">${value}</div><div class="analysis-label">${label}</div></div>`)
    .join("");
}

function renderTable() {
  const designation = $("designationFilter").value;
  const problem = $("problemFilter").value;
  let rows = state.selectedRows;

  if (designation) rows = rows.filter((row) => row.designation === designation);
  if (problem) rows = rows.filter((row) => row.problem === problem);

  if (!rows.length) {
    $("recordsTable").innerHTML = `<tr><td colspan="12" class="empty">没有匹配记录。</td></tr>`;
    return;
  }

  $("recordsTable").innerHTML = rows
    .map((row) => {
      const sourceHref = `${encodeURIComponent(row.source_pdf)}#page=${row.page}`;
      return `
        <tr>
          <td>${escapeHtml(row.team)}</td>
          <td>${displayInstitution(row)}</td>
          <td>${escapeHtml(displayCn(row))}</td>
          <td>${escapeHtml(row.country || "-")}</td>
          <td>${escapeHtml(row.contest)}</td>
          <td>Problem ${escapeHtml(row.problem)}</td>
          <td><strong>${escapeHtml(row.designation)}</strong></td>
          <td>
            <span class="award-badge" style="--badge-color:${COLORS[row.designation] || "#647084"}">
              ${escapeHtml(AWARD_CN[row.designation] || row.designation)}
            </span>
            <span class="specific-award">${escapeHtml(specificAward(row))}</span>
          </td>
          <td>${escapeHtml(row.special_award || "-")}</td>
          <td>${escapeHtml(row.advisor || "-")}</td>
          <td><a href="${sourceHref}" target="_blank" rel="noreferrer">PDF p.${row.page}</a></td>
          <td><a href="${row.certificate_url || `https://www.comap-math.org/mcm/2026Certs/${row.team}.pdf`}" target="_blank" rel="noreferrer">证书</a></td>
        </tr>
      `;
    })
    .join("");
}

function bindSearch() {
  const input = $("schoolSearch");
  input.addEventListener("input", () => renderMatches(input.value));
  input.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const first = getMatches(input.value)[0];
    if (first) selectInstitution(first.key);
  });

  $("clearSearch").addEventListener("click", () => {
    input.value = "";
    state.selectedInstitution = "";
    state.selectedInstitutionKey = "";
    state.selectedRows = [];
    $("schoolTitle").textContent = "请选择一个学校";
    $("schoolCnTitle").textContent = "";
    $("schoolTotal").textContent = "0 teams";
    renderMatches("");
    renderAwardChips();
    renderSchoolCharts();
    renderSchoolAnalysis();
    renderTable();
    input.focus();
  });
}

async function init() {
  const response = await fetch("data/awards-cn.json");
  const data = await response.json();
  state.records = data.records;
  state.summary = data.summary;

  renderSummaryCards();
  setupFilters();
  buildInstitutionIndex();
  bindSearch();
  renderMatches("");
  renderAwardChips();
  renderSchoolCharts();
  renderSchoolAnalysis();
  renderTopChart();

  const requestedSchool = new URLSearchParams(window.location.search).get("school");
  if (requestedSchool) {
    const matches = getMatches(requestedSchool);
    const match = matches.find((item) => item.key === normalize(requestedSchool) || normalize(item.cn) === normalize(requestedSchool)) || matches[0];
    if (match) selectInstitution(match.key);
  }
}

init().catch((error) => {
  console.error(error);
  $("recordsTable").innerHTML = `<tr><td colspan="12" class="empty">数据加载失败，请通过本地 HTTP 服务打开本页。</td></tr>`;
});
