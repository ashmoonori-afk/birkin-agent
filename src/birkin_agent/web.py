from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import urlparse

from .agents import run_agent
from .dashboard import dashboard_data
from .workspace import Workspace


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Birkin Agent Dashboard</title>
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
      grid-template-columns: repeat(5, minmax(0, 1fr));
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
    .status-failed, .severity-critical { background: var(--bad-soft); color: var(--bad); }
    .status-unknown, .severity-warning { background: var(--warn-soft); color: var(--warn); }
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
    .form-row { margin-bottom: 10px; }
    .actions { display: flex; justify-content: flex-end; gap: 8px; }
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
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 6px;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      nav button { margin-bottom: 0; text-align: center; }
      .summary-band, .dashboard-grid { grid-template-columns: 1fr; }
      .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      header { padding: 0 12px; }
      .content { padding: 12px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Birkin Agent Dashboard</h1>
    <span id="root" class="root"></span>
  </header>
  <main>
    <nav>
      <button class="active" data-tab="dashboard">Dashboard</button>
      <button data-tab="jobs">Jobs</button>
      <button data-tab="skills">Skills</button>
      <button data-tab="agents">Agents</button>
      <button data-tab="warnings">Warnings</button>
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
              <h2>Create Job</h2>
              <div class="form-row"><label for="agent">Agent</label><select id="agent"></select></div>
              <div class="form-row"><label for="task">Task</label><textarea id="task">Plan a safe next step for this workspace.</textarea></div>
              <div class="actions"><button class="button" id="build">Run</button></div>
              <pre id="packet"></pre>
            </div>
            <div class="panel">
              <div class="panel-head"><h2>Warnings</h2><span class="muted" id="warning-count"></span></div>
              <table id="warnings-table"></table>
            </div>
          </div>
        </div>
      </section>
      <section id="jobs"><div class="panel"><h2>All Jobs</h2><table id="jobs-full-table"></table></div></section>
      <section id="skills"><div class="panel"><h2>Skills</h2><table id="skills-table"></table></div></section>
      <section id="agents"><div class="panel"><h2>Agents</h2><table id="agents-table"></table></div></section>
      <section id="warnings"><div class="panel"><h2>Warnings</h2><table id="warnings-full-table"></table></div></section>
    </div>
  </main>
  <script>
    const state = { data: null };
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
    async function load() {
      const res = await fetch("/api/status");
      state.data = await res.json();
      const d = state.data;
      document.querySelector("#root").textContent = d.root;
      document.querySelector("#summary").textContent = d.summary;
      document.querySelector("#metric-running").textContent = d.metrics.runningJobs;
      document.querySelector("#metric-completed").textContent = d.metrics.completedJobs;
      document.querySelector("#metric-failed").textContent = d.metrics.failedJobs;
      document.querySelector("#metric-warnings").textContent = d.metrics.warningCount;
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
    }
    document.querySelectorAll("nav button").forEach(button => {
      button.addEventListener("click", () => {
        document.querySelectorAll("nav button, section").forEach(el => el.classList.remove("active"));
        button.classList.add("active");
        document.querySelector("#" + button.dataset.tab).classList.add("active");
      });
    });
    document.querySelector("#build").addEventListener("click", async () => {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify({agent: document.querySelector("#agent").value, task: document.querySelector("#task").value})
      });
      document.querySelector("#packet").textContent = JSON.stringify(await res.json(), null, 2);
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
            task = str(payload.get("task") or "").strip()
            if not agent_id or not task:
                self.send_json({"error": "agent and task are required"}, 400)
                return
            try:
                record, result = run_agent(self.workspace, agent_id, task, execute=False)
            except Exception as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json({"record": str(record), "result": result, "dashboard": dashboard_data(self.workspace)})
            return
        self.send_json({"error": "not found"}, 404)


def serve(workspace: Workspace, host: str = "127.0.0.1", port: int = 8765) -> None:
    class BoundHandler(Handler):
        pass

    BoundHandler.workspace = workspace
    server = ThreadingHTTPServer((host, port), BoundHandler)
    print(f"Birkin Web UI: http://{host}:{port}")
    server.serve_forever()
