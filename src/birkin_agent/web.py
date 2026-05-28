from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import urlparse

from .approvals import approval_rows, approve, reject
from .agents import run_agent
from .chat import run_chat
from .dashboard import dashboard_data
from .learning import approve_learning, learning_proposal_rows, reject_learning, rollback_learning, show_learning_proposal
from .morpheus import run_morpheus
from .workspace import Workspace


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Birkin Agent</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f6f8;
      --panel: #ffffff;
      --line: #d7dde6;
      --text: #16202a;
      --muted: #627083;
      --accent: #0f66b3;
      --accent-soft: #e8f2fb;
      --ok: #137547;
      --ok-soft: #e8f6ef;
      --warn: #9a6500;
      --warn-soft: #fff4d8;
      --bad: #b42318;
      --bad-soft: #fde8e5;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
      letter-spacing: 0;
    }
    header {
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1 { font-size: 18px; margin: 0; font-weight: 700; }
    h2 { font-size: 15px; margin: 0 0 12px 0; }
    main {
      display: grid;
      grid-template-columns: 220px minmax(0, 1fr);
      min-height: calc(100vh - 64px);
    }
    nav {
      padding: 18px 12px;
      border-right: 1px solid var(--line);
      background: #fbfcfd;
    }
    nav button {
      width: 100%;
      min-height: 38px;
      border: 0;
      border-radius: 6px;
      background: transparent;
      color: var(--text);
      text-align: left;
      padding: 9px 10px;
      margin-bottom: 4px;
      font-size: 13px;
      cursor: pointer;
    }
    nav button.active { background: var(--accent-soft); color: #084b83; font-weight: 700; }
    body.lite:not(.show-advanced) nav button[data-advanced="true"] { display: none; }
    body.lite:not(.show-advanced) .advanced-control { display: none; }
    #advanced-toggle {
      margin-top: 10px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--muted);
      text-align: center;
    }
    .content { padding: 18px; min-width: 0; }
    section { display: none; }
    section.active { display: block; }
    .summary-band {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      gap: 12px;
      margin-bottom: 14px;
    }
    .summary, .panel, .metric {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
    }
    .summary { padding: 16px; }
    .summary p { margin: 0; color: var(--muted); line-height: 1.5; font-size: 13px; }
    .root { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .metrics {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }
    .metric { padding: 13px; min-height: 86px; }
    .metric .label { color: var(--muted); font-size: 12px; }
    .metric .value { font-size: 26px; margin-top: 8px; font-weight: 700; }
    .metric .detail { color: var(--muted); font-size: 12px; margin-top: 4px; }
    .dashboard-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      gap: 14px;
      align-items: start;
    }
    .panel { padding: 14px; margin-bottom: 14px; overflow: hidden; }
    .panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 10px;
    }
    table { width: 100%; border-collapse: collapse; }
    th, td {
      padding: 9px 8px;
      border-bottom: 1px solid var(--line);
      font-size: 12px;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }
    th { color: var(--muted); font-weight: 700; background: #f8fafc; }
    tr:last-child td { border-bottom: 0; }
    .chip {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .status-running { background: var(--accent-soft); color: #084b83; }
    .status-ok, .status-packet-only { background: var(--ok-soft); color: var(--ok); }
    .status-failed, .status-error, .severity-critical { background: var(--bad-soft); color: var(--bad); }
    .status-warning, .status-unknown, .severity-warning { background: var(--warn-soft); color: var(--warn); }
    label { display: block; color: var(--muted); font-size: 12px; margin-bottom: 6px; }
    select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      font-size: 13px;
      padding: 9px;
    }
    textarea { min-height: 112px; resize: vertical; }
    input[type="checkbox"] { margin-right: 6px; }
    .form-row { margin-bottom: 10px; }
    .actions { display: flex; justify-content: flex-end; gap: 8px; }
    .chat-layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 300px;
      gap: 14px;
      align-items: start;
    }
    .chat-thread {
      min-height: 440px;
      max-height: calc(100vh - 240px);
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfcfd;
      padding: 12px;
    }
    .message {
      max-width: 78%;
      margin-bottom: 10px;
      padding: 10px 12px;
      border-radius: 6px;
      font-size: 13px;
      line-height: 1.45;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }
    .message.user { margin-left: auto; background: var(--accent); color: #fff; }
    .message.assistant { margin-right: auto; background: #fff; border: 1px solid var(--line); }
    .chat-input { min-height: 120px; }
    .button {
      border: 1px solid #0b5b9d;
      background: var(--accent);
      color: #fff;
      border-radius: 6px;
      padding: 9px 13px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
    }
    pre {
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: #111827;
      color: #edf2f7;
      border-radius: 6px;
      padding: 10px;
      max-height: 280px;
      overflow: auto;
      font-size: 12px;
    }
    .empty { color: var(--muted); font-size: 13px; padding: 10px 0; }
    .muted { color: var(--muted); }
    @media (max-width: 980px) {
      main { grid-template-columns: 1fr; }
      nav {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 6px;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      nav button { margin-bottom: 0; text-align: center; }
      .summary-band, .dashboard-grid, .chat-layout { grid-template-columns: 1fr; }
      .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      header { padding: 0 12px; }
      .content { padding: 12px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Birkin Agent</h1>
    <span id="root" class="root"></span>
  </header>
  <main>
    <nav>
      <button class="active" data-tab="dashboard">Dashboard</button>
      <button data-tab="chat">Chat</button>
      <button data-tab="setup">Setup</button>
      <button data-tab="jobs">Jobs</button>
      <button data-tab="models" data-advanced="true">Models</button>
      <button data-tab="auth" data-advanced="true">Auth</button>
      <button data-tab="api" data-advanced="true">API</button>
      <button data-tab="gateway" data-advanced="true">Gateway</button>
      <button data-tab="memory">Memory</button>
      <button data-tab="ledger" data-advanced="true">Ledger</button>
      <button data-tab="telegram" data-advanced="true">Telegram</button>
      <button data-tab="approvals" data-advanced="true">Approvals</button>
      <button data-tab="learning" data-advanced="true">Learning</button>
      <button data-tab="reliability" data-advanced="true">Reliability</button>
      <button data-tab="morpheus" data-advanced="true">Morpheus</button>
      <button data-tab="skills">Skills</button>
      <button data-tab="agents" data-advanced="true">Agents</button>
      <button data-tab="warnings">Warnings</button>
      <button id="advanced-toggle" type="button">Show Advanced</button>
    </nav>
    <div class="content">
      <section id="dashboard" class="active">
        <div class="summary-band">
          <div class="summary">
            <h2>Workspace Summary</h2>
            <p id="summary"></p>
          </div>
          <div class="panel">
            <h2>Usage</h2>
            <div id="usage"></div>
          </div>
        </div>
        <div class="metrics">
          <div class="metric"><div class="label">Running Jobs</div><div class="value" id="metric-running">0</div><div class="detail">active records</div></div>
          <div class="metric"><div class="label">Completed</div><div class="value" id="metric-completed">0</div><div class="detail">ok or packet-only</div></div>
          <div class="metric"><div class="label">Failed</div><div class="value" id="metric-failed">0</div><div class="detail">needs review</div></div>
          <div class="metric"><div class="label">Warnings</div><div class="value" id="metric-warnings">0</div><div class="detail">shown separately</div></div>
          <div class="metric"><div class="label">Models</div><div class="value" id="metric-models">0</div><div class="detail">selectable profiles</div></div>
          <div class="metric"><div class="label">Skills</div><div class="value" id="metric-skills">0</div><div class="detail" id="metric-skills-detail"></div></div>
        </div>
        <div class="dashboard-grid">
          <div>
            <div class="panel">
              <div class="panel-head"><h2>Running Jobs</h2><span class="muted" id="running-count"></span></div>
              <table id="running-table"></table>
            </div>
            <div class="panel">
              <div class="panel-head"><h2>Recent Job Results</h2><span class="muted" id="job-count"></span></div>
              <table id="jobs-table"></table>
            </div>
          </div>
          <div>
            <div class="panel">
              <h2>Try Safe Packet</h2>
              <div class="form-row"><label for="agent">Agent</label><select id="agent"></select></div>
              <div class="form-row"><label for="model">Model</label><select id="model"></select></div>
              <div class="form-row"><label for="task">Task</label><textarea id="task">Plan a safe next step for this workspace.</textarea></div>
              <div class="form-row advanced-control"><label><input id="execute" type="checkbox">Execute selected runner</label></div>
              <div class="actions"><button class="button" id="build">Build Packet</button></div>
              <pre id="packet"></pre>
            </div>
            <div class="panel">
              <div class="panel-head"><h2>Warnings</h2><span class="muted" id="warning-count"></span></div>
              <table id="warnings-table"></table>
            </div>
          </div>
        </div>
      </section>
      <section id="chat">
        <div class="chat-layout">
          <div class="panel">
            <div class="panel-head"><h2>Chat</h2><span class="muted" id="chat-status"></span></div>
            <div id="chat-thread" class="chat-thread"></div>
          </div>
          <div class="panel">
            <h2>Message</h2>
            <div class="form-row"><label for="chat-agent">Agent</label><select id="chat-agent"></select></div>
            <div class="form-row"><label for="chat-model">Model</label><select id="chat-model"></select></div>
            <div class="form-row"><label for="chat-message">Message</label><textarea id="chat-message" class="chat-input"></textarea></div>
            <div class="form-row advanced-control"><label><input id="chat-execute" type="checkbox">Execute selected runner</label></div>
            <div class="actions"><button class="button" id="chat-send">Send</button></div>
          </div>
        </div>
      </section>
      <section id="setup"><div class="panel"><h2>Setup</h2><table id="setup-table"></table></div><div class="panel"><h2>Skill Config</h2><table id="skill-config-table"></table></div></section>
      <section id="jobs"><div class="panel"><h2>All Jobs</h2><table id="jobs-full-table"></table></div></section>
      <section id="models"><div class="panel"><h2>Models</h2><table id="models-table"></table></div></section>
      <section id="auth"><div class="panel"><h2>Auth</h2><table id="auth-table"></table></div></section>
      <section id="api"><div class="panel"><h2>API Profiles</h2><table id="api-table"></table></div></section>
      <section id="gateway"><div class="panel"><h2>Gateway</h2><pre id="gateway-json"></pre></div></section>
      <section id="memory"><div class="panel"><h2>Memory</h2><table id="memory-table"></table></div></section>
      <section id="ledger"><div class="panel"><h2>Ledger Summary</h2><pre id="ledger-json"></pre></div><div class="panel"><h2>Ledger Rows</h2><table id="ledger-table"></table></div></section>
      <section id="telegram"><div class="panel"><h2>Telegram</h2><table id="telegram-table"></table></div></section>
      <section id="approvals"><div class="panel"><h2>Pending Approvals</h2><table id="approvals-table"></table></div></section>
      <section id="learning"><div class="panel"><h2>Verified Learning Proposals</h2><table id="learning-table"></table><pre id="learning-detail"></pre></div><div class="panel"><h2>Learning Events</h2><table id="learning-events-table"></table></div></section>
      <section id="reliability"><div class="panel"><h2>Health</h2><table id="health-table"></table></div><div class="panel"><h2>Budget</h2><pre id="budget-json"></pre></div><div class="panel"><h2>Trace Timeline</h2><table id="traces-table"></table></div><div class="panel"><h2>Replay Records</h2><table id="replays-table"></table></div><div class="panel"><h2>Delivery / Reliability Log</h2><table id="reliability-table"></table></div></section>
      <section id="morpheus"><div class="panel"><div class="panel-head"><h2>Morpheus</h2><button class="button" id="morpheus-dry-run">Dry Run</button></div><pre id="morpheus-json"></pre><pre id="morpheus-result"></pre></div><div class="panel"><h2>Schedules</h2><table id="schedules-table"></table></div><div class="panel"><h2>Daemon</h2><pre id="daemon-json"></pre></div></section>
      <section id="skills"><div class="panel"><h2>Skills</h2><table id="skills-table"></table></div></section>
      <section id="agents"><div class="panel"><h2>Agents</h2><table id="agents-table"></table></div></section>
      <section id="warnings"><div class="panel"><h2>Warnings</h2><table id="warnings-full-table"></table></div></section>
    </div>
  </main>
  <script>
    const state = { data: null, chatMessages: [] };
    function esc(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }
    function safeClass(value) {
      return String(value ?? "unknown").toLowerCase().replace(/[^a-z0-9_-]+/g, "-") || "unknown";
    }
    function statusChip(status) {
      return `<span class="chip status-${safeClass(status)}">${esc(status || "unknown")}</span>`;
    }
    function severityChip(severity) {
      return `<span class="chip severity-${safeClass(severity)}">${esc(severity)}</span>`;
    }
    function advancedEnabled() {
      return !document.body.classList.contains("lite") || document.body.classList.contains("show-advanced");
    }
    function renderChat() {
      const thread = document.querySelector("#chat-thread");
      if (!state.chatMessages.length) {
        thread.innerHTML = `<div class="empty">No messages.</div>`;
        return;
      }
      thread.innerHTML = state.chatMessages.map(item => {
        const role = item.role === "user" ? "user" : "assistant";
        return `<div class="message ${role}">${esc(item.content)}</div>`;
      }).join("");
      thread.scrollTop = thread.scrollHeight;
    }
    function renderUsage(usage) {
      const box = document.createElement("div");
      box.className = "metric";
      const label = document.createElement("div");
      label.className = "label";
      label.textContent = "Estimated Prompt Tokens";
      const value = document.createElement("div");
      value.className = "value";
      value.textContent = usage.estimatedTokens;
      const detail = document.createElement("div");
      detail.className = "detail";
      detail.textContent = `${usage.runs} job records`;
      box.append(label, value, detail);
      document.querySelector("#usage").replaceChildren(box);
    }
    function table(el, rows, columns, renderers = {}) {
      if (!rows.length) { el.innerHTML = `<tr><td class="empty" colspan="${columns.length}">No rows.</td></tr>`; return; }
      const head = "<tr>" + columns.map(c => `<th>${esc(c.label)}</th>`).join("") + "</tr>";
      const body = rows.map(row => "<tr>" + columns.map(c => {
        const raw = row[c.key];
        const value = renderers[c.key] ? renderers[c.key](raw, row) : esc(raw);
        return `<td>${value}</td>`;
      }).join("") + "</tr>").join("");
      el.innerHTML = head + body;
    }
    function jobColumns() {
      return [
        {key: "status", label: "Status"},
        {key: "agent", label: "Agent"},
        {key: "model", label: "Model"},
        {key: "task", label: "Task"},
        {key: "summary", label: "Result Summary"},
        {key: "usage", label: "Usage"},
        {key: "timestamp", label: "Updated"}
      ];
    }
    function renderJobs(el, rows) {
      table(el, rows, jobColumns(), {
        status: statusChip,
        task: value => esc(String(value).slice(0, 110)),
        summary: value => esc(String(value).slice(0, 180)),
        usage: usage => esc(`${usage?.estimatedTokens ?? 0} est tok / ${usage?.skills ?? 0} skills`)
      });
    }
    function renderWarnings(el, rows) {
      table(el, rows, [
        {key: "severity", label: "Severity"},
        {key: "source", label: "Source"},
        {key: "message", label: "Warning"}
      ], { severity: severityChip });
    }
    function renderApprovals(el, rows) {
      if (!rows.length) { el.innerHTML = `<tr><td class="empty" colspan="10">No pending approvals.</td></tr>`; return; }
      const head = "<tr><th>Risk</th><th>Category</th><th>Title</th><th>Origin</th><th>Status</th><th>Resources</th><th>Evidence</th><th>Dry Run</th><th>Rollback</th><th>Action</th></tr>";
      const body = rows.map(row => `<tr>
        <td>${statusChip(row.riskTier)}</td>
        <td>${esc(row.category)}</td>
        <td>${esc(row.title)}</td>
        <td>${esc(row.origin)}</td>
        <td>${statusChip(row.status)}</td>
        <td>${esc(row.resources)}</td>
        <td>${esc(row.evidence)}</td>
        <td>${esc(row.dryRun)}</td>
        <td>${esc(row.rollback)}</td>
        <td><button class="button" onclick="resolveApproval('${esc(row.id)}','approve')">Approve</button> <button class="button" onclick="resolveApproval('${esc(row.id)}','reject')">Reject</button></td>
      </tr>`).join("");
      el.innerHTML = head + body;
    }
    function renderLearning(el, rows) {
      if (!rows.length) { el.innerHTML = `<tr><td class="empty" colspan="9">No pending learning proposals.</td></tr>`; return; }
      const head = "<tr><th>Risk</th><th>Target</th><th>Action</th><th>Confidence</th><th>Evidence</th><th>Reason</th><th>Created</th><th>ID</th><th>Action</th></tr>";
      const body = rows.map(row => `<tr>
        <td>${statusChip(row.riskTier)}</td>
        <td>${esc(row.targetType)}:${esc(row.target)}</td>
        <td>${esc(row.action)}</td>
        <td>${esc(row.confidence)}</td>
        <td>${esc(row.evidence)}</td>
        <td>${esc(row.reason)}</td>
        <td>${esc(row.created)}</td>
        <td>${esc(row.id)}</td>
        <td><button class="button" onclick="resolveLearning('${esc(row.id)}','show')">Show</button> <button class="button" onclick="resolveLearning('${esc(row.id)}','approve')">Approve</button> <button class="button" onclick="resolveLearning('${esc(row.id)}','reject')">Reject</button></td>
      </tr>`).join("");
      el.innerHTML = head + body;
    }
    function renderLearningEvents(el, rows) {
      if (!rows.length) { el.innerHTML = `<tr><td class="empty" colspan="9">No learning events.</td></tr>`; return; }
      const head = "<tr><th>Timestamp</th><th>Status</th><th>Action</th><th>Type</th><th>Target</th><th>Confidence</th><th>Evidence</th><th>Reason</th><th>Rollback</th></tr>";
      const body = rows.map(row => `<tr>
        <td>${esc(row.timestamp)}</td>
        <td>${statusChip(row.status)}</td>
        <td>${esc(row.action)}</td>
        <td>${esc(row.targetType)}</td>
        <td>${esc(row.target)}</td>
        <td>${esc(row.confidence)}</td>
        <td>${esc(row.evidenceStrength)}</td>
        <td>${esc(row.reason)}</td>
        <td><button class="button" onclick="resolveLearning('${esc(row.id)}','rollback')">Rollback</button></td>
      </tr>`).join("");
      el.innerHTML = head + body;
    }
    async function resolveApproval(id, action) {
      await fetch("/api/approvals", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify({id, action})
      });
      await load();
    }
    async function resolveLearning(id, action) {
      const res = await fetch("/api/learning", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify({id, action})
      });
      const payload = await res.json();
      if (action === "show" || payload.error) {
        document.querySelector("#learning-detail").textContent = JSON.stringify(payload, null, 2);
      }
      await load();
    }
    async function load() {
      const res = await fetch("/api/status");
      state.data = await res.json();
      const d = state.data;
      const isLite = (d.experience?.mode || "lite") === "lite";
      document.body.classList.toggle("lite", isLite);
      const advancedToggle = document.querySelector("#advanced-toggle");
      advancedToggle.style.display = isLite ? "" : "none";
      advancedToggle.textContent = document.body.classList.contains("show-advanced") ? "Hide Advanced" : "Show Advanced";
      document.querySelector("#root").textContent = `${d.root} - ${d.experience?.mode || "lite"}`;
      document.querySelector("#summary").textContent = d.summary;
      document.querySelector("#metric-running").textContent = d.metrics.runningJobs;
      document.querySelector("#metric-completed").textContent = d.metrics.completedJobs;
      document.querySelector("#metric-failed").textContent = d.metrics.failedJobs;
      document.querySelector("#metric-warnings").textContent = d.metrics.warningCount;
      document.querySelector("#metric-models").textContent = d.metrics.modelsTotal;
      document.querySelector("#metric-models").nextElementSibling.textContent = `${d.metrics.authProfiles} auth / ${d.metrics.apiProfiles} api`;
      document.querySelector("#metric-skills").textContent = d.metrics.skillsEnabled;
      document.querySelector("#metric-skills-detail").textContent = `${d.metrics.skillsTotal} total`;
      renderUsage(d.usage);
      const running = d.jobs.filter(job => job.status === "running");
      document.querySelector("#running-count").textContent = `${running.length} active`;
      document.querySelector("#job-count").textContent = `${d.jobs.length} records`;
      document.querySelector("#warning-count").textContent = `${d.warnings.length} items`;
      renderJobs(document.querySelector("#running-table"), running);
      renderJobs(document.querySelector("#jobs-table"), d.jobs.slice(0, 8));
      renderJobs(document.querySelector("#jobs-full-table"), d.jobs);
      renderWarnings(document.querySelector("#warnings-table"), d.warnings.slice(0, 8));
      renderWarnings(document.querySelector("#warnings-full-table"), d.warnings);
      table(document.querySelector("#models-table"), d.models, [
        {key: "id", label: "ID"},
        {key: "default", label: "Default"},
        {key: "provider", label: "Provider"},
        {key: "model", label: "Model"},
        {key: "runner", label: "Runner"},
        {key: "apiProfile", label: "API Profile"},
        {key: "command", label: "Command"},
        {key: "description", label: "Description"}
      ]);
      table(document.querySelector("#setup-table"), d.setup.checks, [
        {key: "step", label: "Step"},
        {key: "status", label: "Status"},
        {key: "detail", label: "Detail"},
        {key: "command", label: "Command"}
      ], { status: statusChip });
      table(document.querySelector("#skill-config-table"), d.skillConfig, [
        {key: "check", label: "Check"},
        {key: "status", label: "Status"},
        {key: "detail", label: "Detail"}
      ], { status: statusChip });
      table(document.querySelector("#auth-table"), d.auth, [
        {key: "id", label: "ID"},
        {key: "type", label: "Type"},
        {key: "provider", label: "Provider"},
        {key: "binary", label: "Binary"},
        {key: "available", label: "Available"},
        {key: "required", label: "Required"},
        {key: "description", label: "Description"}
      ]);
      table(document.querySelector("#api-table"), d.api, [
        {key: "id", label: "ID"},
        {key: "type", label: "Type"},
        {key: "baseUrl", label: "Base URL"},
        {key: "apiKeyEnv", label: "Key Env"},
        {key: "keyPresent", label: "Key Present"},
        {key: "chatPath", label: "Chat Path"},
        {key: "description", label: "Description"}
      ]);
      document.querySelector("#gateway-json").textContent = JSON.stringify(d.gateway, null, 2);
      table(document.querySelector("#memory-table"), [d.memory], [
        {key: "provider", label: "Provider"},
        {key: "vaultPath", label: "Vault"},
        {key: "vaultExists", label: "Exists"},
        {key: "noteCount", label: "Notes"},
        {key: "error", label: "Error"}
      ]);
      document.querySelector("#ledger-json").textContent = JSON.stringify(d.ledger, null, 2);
      table(document.querySelector("#ledger-table"), d.ledgerRows, [
        {key: "timestamp", label: "Timestamp"},
        {key: "runId", label: "Run"},
        {key: "agent", label: "Agent"},
        {key: "status", label: "Status"},
        {key: "model", label: "Model"},
        {key: "estimatedTokens", label: "Est Tokens"},
        {key: "providerTokens", label: "Provider Tokens"},
        {key: "costUsd", label: "Cost USD"}
      ]);
      table(document.querySelector("#telegram-table"), [d.telegram], [
        {key: "enabled", label: "Enabled"},
        {key: "botTokenEnv", label: "Token Env"},
        {key: "tokenPresent", label: "Token Present"},
        {key: "chatId", label: "Chat ID"},
        {key: "parseMode", label: "Parse Mode"},
        {key: "inboundEnabled", label: "Inbound"}
      ]);
      renderApprovals(document.querySelector("#approvals-table"), d.approvals || []);
      renderLearning(document.querySelector("#learning-table"), d.learningProposals || []);
      renderLearningEvents(document.querySelector("#learning-events-table"), d.learningEvents || []);
      table(document.querySelector("#health-table"), d.health || [], [
        {key: "name", label: "Name"},
        {key: "status", label: "Status"},
        {key: "detail", label: "Detail"}
      ], { status: statusChip });
      document.querySelector("#budget-json").textContent = JSON.stringify(d.budget || {}, null, 2);
      table(document.querySelector("#traces-table"), d.traces || [], [
        {key: "timestamp", label: "Timestamp"},
        {key: "traceId", label: "Trace"},
        {key: "stage", label: "Stage"},
        {key: "status", label: "Status"},
        {key: "resource", label: "Resource"},
        {key: "message", label: "Message"}
      ], { status: statusChip });
      table(document.querySelector("#replays-table"), d.replays || [], [
        {key: "timestamp", label: "Timestamp"},
        {key: "traceId", label: "Trace"},
        {key: "status", label: "Status"},
        {key: "resource", label: "Resource"},
        {key: "replayable", label: "Replayable"},
        {key: "message", label: "Message"}
      ], { status: statusChip });
      table(document.querySelector("#reliability-table"), d.reliability || [], [
        {key: "timestamp", label: "Timestamp"},
        {key: "traceId", label: "Trace"},
        {key: "stage", label: "Stage"},
        {key: "status", label: "Status"},
        {key: "resource", label: "Resource"},
        {key: "message", label: "Message"}
      ], { status: statusChip });
      document.querySelector("#morpheus-json").textContent = JSON.stringify(d.morpheus || {}, null, 2);
      document.querySelector("#daemon-json").textContent = JSON.stringify(d.daemon || {}, null, 2);
      table(document.querySelector("#schedules-table"), d.schedules || [], [
        {key: "id", label: "ID"},
        {key: "name", label: "Name"},
        {key: "hour", label: "Hour"},
        {key: "minute", label: "Minute"},
        {key: "action", label: "Action"},
        {key: "created", label: "Created"}
      ]);
      table(document.querySelector("#skills-table"), d.skills, [
        {key: "name", label: "Name"},
        {key: "enabled", label: "Enabled"},
        {key: "source", label: "Source"},
        {key: "description", label: "Description"},
        {key: "reason", label: "Reason"}
      ]);
      table(document.querySelector("#agents-table"), d.agents, [
        {key: "id", label: "ID"},
        {key: "runner", label: "Runner"},
        {key: "model", label: "Model"},
        {key: "skills", label: "Skills"},
        {key: "role", label: "Role"}
      ]);
      const agentSelect = document.querySelector("#agent");
      agentSelect.replaceChildren(...d.agents.map(a => {
        const option = document.createElement("option");
        option.value = a.id;
        option.textContent = a.id;
        return option;
      }));
      const modelSelect = document.querySelector("#model");
      modelSelect.replaceChildren(...d.models.map(m => {
        const option = document.createElement("option");
        option.value = m.id;
        option.textContent = m.default === "yes" ? `${m.id} (default)` : m.id;
        return option;
      }));
      const chatAgent = document.querySelector("#chat-agent");
      chatAgent.replaceChildren(...d.agents.map(a => {
        const option = document.createElement("option");
        option.value = a.id;
        option.textContent = a.id;
        if (a.id === "chat") option.selected = true;
        return option;
      }));
      const chatModel = document.querySelector("#chat-model");
      chatModel.replaceChildren(...d.models.map(m => {
        const option = document.createElement("option");
        option.value = m.id;
        option.textContent = m.default === "yes" ? `${m.id} (default)` : m.id;
        return option;
      }));
      renderChat();
    }
    document.querySelectorAll("nav button[data-tab]").forEach(button => {
      button.addEventListener("click", () => {
        document.querySelectorAll("nav button[data-tab], section").forEach(el => el.classList.remove("active"));
        button.classList.add("active");
        document.querySelector("#" + button.dataset.tab).classList.add("active");
      });
    });
    document.querySelector("#advanced-toggle").addEventListener("click", () => {
      document.body.classList.toggle("show-advanced");
      document.querySelector("#advanced-toggle").textContent =
        document.body.classList.contains("show-advanced") ? "Hide Advanced" : "Show Advanced";
    });
    document.querySelector("#build").addEventListener("click", async () => {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify({
          agent: document.querySelector("#agent").value,
          model: document.querySelector("#model").value,
          task: document.querySelector("#task").value,
          execute: advancedEnabled() && document.querySelector("#execute").checked
        })
      });
      document.querySelector("#packet").textContent = JSON.stringify(await res.json(), null, 2);
      await load();
    });
    document.querySelector("#chat-send").addEventListener("click", async () => {
      const input = document.querySelector("#chat-message");
      const message = input.value.trim();
      if (!message) return;
      const history = state.chatMessages.slice(-12);
      state.chatMessages.push({role: "user", content: message});
      input.value = "";
      document.querySelector("#chat-status").textContent = "Sending";
      renderChat();
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify({
          agent: document.querySelector("#chat-agent").value,
          model: document.querySelector("#chat-model").value,
          message,
          history,
          execute: advancedEnabled() && document.querySelector("#chat-execute").checked
        })
      });
      const payload = await res.json();
      if (payload.error) {
        state.chatMessages.push({role: "assistant", content: payload.error});
        document.querySelector("#chat-status").textContent = "Error";
      } else {
        state.chatMessages.push({role: "assistant", content: payload.reply});
        document.querySelector("#chat-status").textContent = payload.status;
      }
      renderChat();
      await load();
    });
    document.querySelector("#morpheus-dry-run").addEventListener("click", async () => {
      const res = await fetch("/api/morpheus", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify({dryRun: true})
      });
      document.querySelector("#morpheus-result").textContent = JSON.stringify(await res.json(), null, 2);
      await load();
    });
    load();
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    workspace: Workspace

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def require_local_request(self) -> bool:
        host = self.client_address[0] if self.client_address else ""
        if host in {"127.0.0.1", "::1", "localhost"}:
            return True
        self.send_json({"error": "local request required"}, 403)
        return False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            data = INDEX_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if parsed.path == "/api/status":
            self.send_json(dashboard_data(self.workspace))
            return
        if parsed.path == "/api/learning":
            self.send_json({"proposals": learning_proposal_rows(self.workspace)})
            return
        self.send_json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self.send_json({"error": "invalid json"}, 400)
            return
        if parsed.path == "/api/run":
            agent_id = str(payload.get("agent") or "").strip()
            model = str(payload.get("model") or "").strip() or None
            provider = str(payload.get("provider") or "").strip() or None
            runner = str(payload.get("runner") or "").strip() or None
            task = str(payload.get("task") or "").strip()
            execute = bool(payload.get("execute") or False)
            include_skill_bodies = bool(payload.get("includeSkillBodies") or False)
            if not agent_id or not task:
                self.send_json({"error": "agent and task are required"}, 400)
                return
            try:
                record, result = run_agent(
                    self.workspace,
                    agent_id,
                    task,
                    runner_name=runner,
                    model_name=model,
                    provider_name=provider,
                    include_skill_bodies=include_skill_bodies,
                    execute=execute,
                )
            except Exception as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json({"record": str(record), "result": result, "dashboard": dashboard_data(self.workspace)})
            return
        if parsed.path == "/api/chat":
            agent_id = str(payload.get("agent") or "").strip() or None
            model = str(payload.get("model") or "").strip() or None
            provider = str(payload.get("provider") or "").strip() or None
            message = str(payload.get("message") or "").strip()
            history = payload.get("history") if isinstance(payload.get("history"), list) else []
            execute = bool(payload.get("execute") or False)
            if not message:
                self.send_json({"error": "message is required"}, 400)
                return
            try:
                chat = run_chat(
                    self.workspace,
                    message,
                    agent_id=agent_id,
                    model_name=model,
                    provider_name=provider,
                    execute=execute,
                    history=history,
                )
            except Exception as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            chat["dashboard"] = dashboard_data(self.workspace)
            self.send_json(chat)
            return
        if parsed.path == "/api/approvals":
            if not self.require_local_request():
                return
            action = str(payload.get("action") or "").strip().lower()
            approval_id = str(payload.get("id") or "").strip()
            if action not in {"approve", "reject"} or not approval_id:
                self.send_json({"error": "action approve/reject and id are required"}, 400)
                return
            try:
                result = approve(self.workspace, approval_id) if action == "approve" else reject(self.workspace, approval_id)
            except Exception as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json({"approval": result, "approvals": approval_rows(self.workspace)})
            return
        if parsed.path == "/api/learning":
            if not self.require_local_request():
                return
            action = str(payload.get("action") or "").strip().lower()
            proposal_id = str(payload.get("id") or "").strip()
            if action not in {"approve", "reject", "show", "rollback"} or not proposal_id:
                self.send_json({"error": "action approve/reject/show/rollback and id are required"}, 400)
                return
            try:
                if action == "approve":
                    result = approve_learning(self.workspace, proposal_id)
                elif action == "reject":
                    result = reject_learning(self.workspace, proposal_id)
                elif action == "show":
                    result = show_learning_proposal(self.workspace, proposal_id)
                else:
                    result = rollback_learning(self.workspace, proposal_id)
            except Exception as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json({"learning": result, "proposals": learning_proposal_rows(self.workspace)})
            return
        if parsed.path in ["/api/morpheus", "/api/nightly"]:
            if not self.require_local_request():
                return
            try:
                result = run_morpheus(self.workspace, dry_run=bool(payload.get("dryRun", True)))
            except Exception as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json({"morpheus": result, "dashboard": dashboard_data(self.workspace)})
            return
        self.send_json({"error": "not found"}, 404)


def serve(workspace: Workspace, host: str = "127.0.0.1", port: int = 8765) -> None:
    class BoundHandler(Handler):
        pass

    BoundHandler.workspace = workspace
    server = ThreadingHTTPServer((host, port), BoundHandler)
    print(f"Birkin Web UI: http://{host}:{port}")
    server.serve_forever()
