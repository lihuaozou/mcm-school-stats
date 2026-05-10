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

const state = {
  records: [],
  summary: null,
  institutions: [],
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
    if (!groups.has(key)) groups.set(key, { key, count: 0, variants: new Map() });
    const group = groups.get(key);
    group.count += 1;
    group.variants.set(row.institution, (group.variants.get(row.institution) || 0) + 1);
  });

  state.institutions = [...groups.values()]
    .map((group) => {
      const variants = [...group.variants.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
      return { ...group, name: variants[0][0], variantNames: variants.map(([name]) => name) };
    })
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));

  $("schoolSuggestions").innerHTML = state.institutions
    .slice(0, 700)
    .map((item) => `<option value="${escapeHtml(item.name)}"></option>`)
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
    "注：Problem A 的官方首页摘要为 8,574 队，逐行名单抽取为 8,575 队；页面保留逐行名单用于学校查询，其余题目与官方摘要一致。";
}

function getMatches(query) {
  const q = normalize(query);
  if (!q) return state.institutions.slice(0, 8);

  const starts = [];
  const contains = [];
  state.institutions.forEach((item) => {
    if (item.key.startsWith(q)) starts.push(item);
    else if (item.key.includes(q)) contains.push(item);
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
          <span class="match-name">${escapeHtml(item.name)}</span>
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
  $("schoolTotal").textContent = `${fmt.format(state.selectedRows.length)} teams`;
  $("designationFilter").value = "";
  $("problemFilter").value = "";

  renderMatches(state.selectedInstitution);
  renderAwardChips();
  renderSchoolCharts();
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
}

function renderTopChart() {
  const items = state.summary.top_institutions.slice(0, 20).map(([label, value]) => ({ label, value }));
  drawHorizontalBarChart($("topChart"), items);
}

function renderTable() {
  const designation = $("designationFilter").value;
  const problem = $("problemFilter").value;
  let rows = state.selectedRows;

  if (designation) rows = rows.filter((row) => row.designation === designation);
  if (problem) rows = rows.filter((row) => row.problem === problem);

  if (!rows.length) {
    $("recordsTable").innerHTML = `<tr><td colspan="11" class="empty">没有匹配记录。</td></tr>`;
    return;
  }

  $("recordsTable").innerHTML = rows
    .map((row) => {
      const sourceHref = `${encodeURIComponent(row.source_pdf)}#page=${row.page}`;
      return `
        <tr>
          <td>${escapeHtml(row.team)}</td>
          <td>${displayInstitution(row)}</td>
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
    $("schoolTotal").textContent = "0 teams";
    renderMatches("");
    renderAwardChips();
    renderSchoolCharts();
    renderTable();
    input.focus();
  });
}

async function init() {
  const response = await fetch("data/awards.json");
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
  renderTopChart();

  const requestedSchool = new URLSearchParams(window.location.search).get("school");
  if (requestedSchool) {
    const match = getMatches(requestedSchool).find((item) => item.key === normalize(requestedSchool));
    if (match) selectInstitution(match.key);
  }
}

init().catch((error) => {
  console.error(error);
  $("recordsTable").innerHTML = `<tr><td colspan="11" class="empty">数据加载失败，请通过本地 HTTP 服务打开本页。</td></tr>`;
});
