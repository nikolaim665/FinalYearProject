"""
Generate a self-contained HTML report from batch_eval.json.
Usage: python3 show_eval.py [batch_eval.json] [output.html]
"""
import json
import sys
from pathlib import Path

INPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("batch_eval.json")
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("eval_report.html")

with open(INPUT) as f:
    data = json.load(f)

g = data["global_summary"]
samples = data["per_sample"]

METRICS = ["accuracy", "clarity", "pedagogical_value", "code_specificity", "difficulty_calibration"]
LABELS = ["Accuracy", "Clarity", "Pedagogical Value", "Code Specificity", "Difficulty Calib."]


def score_color(score):
    if score >= 4.5:
        return "#22c55e"
    elif score >= 3.5:
        return "#eab308"
    else:
        return "#ef4444"


def bar(score, max_score=5):
    pct = score / max_score * 100
    color = score_color(score)
    score_fmt = "{:.2f}".format(score)
    return (
        '<div style="display:flex;align-items:center;gap:8px">'
        '<div style="background:#e5e7eb;border-radius:4px;height:10px;width:120px;flex-shrink:0">'
        '<div style="background:{color};height:100%;width:{pct}%;border-radius:4px"></div>'
        '</div>'
        '<span style="font-weight:600;color:{color}">{score}</span>'
        '</div>'
    ).replace("{color}", color).replace("{pct}", "{:.1f}".format(pct)).replace("{score}", score_fmt)


def build_question_rows(questions):
    parts = []
    for q in questions:
        score_cells = ""
        for m in METRICS:
            v = q["scores"].get(m, 0)
            score_cells += '<td style="padding:6px 8px;text-align:center"><span style="color:{c};font-weight:600">{v}</span></td>'.format(
                c=score_color(v), v=v
            )
        overall_fmt = "{:.2f}".format(q["overall_score"])
        flagged_cell = '<span style="color:#dc2626">Yes</span>' if q["is_flagged"] else '<span style="color:#16a34a">No</span>'
        parts.append(
            '<tr style="border-top:1px solid #e2e8f0">'
            '<td style="padding:6px 8px;color:#6366f1">{qid}</td>'
            '<td style="padding:6px 8px;max-width:300px">{qt}</td>'
            '{scores}'
            '<td style="padding:6px 8px;text-align:center"><span style="color:{oc};font-weight:600">{ov}</span></td>'
            '<td style="padding:6px 8px;text-align:center">{flagged}</td>'
            '</tr>'
            '<tr><td colspan="10" style="padding:4px 8px 10px 8px;color:#6b7280;font-size:11px;font-style:italic">{expl}</td></tr>'.format(
                qid=q["question_id"],
                qt=q["question_text"],
                scores=score_cells,
                oc=score_color(q["overall_score"]),
                ov=overall_fmt,
                flagged=flagged_cell,
                expl=q["explanation"].replace("<", "&lt;").replace(">", "&gt;"),
            )
        )
    return "".join(parts)


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_sample_rows(samples):
    parts = []
    for s in samples:
        if "summary" not in s:
            error_msg = s.get("error", "Unknown error")
            parts.append(
                '<tr class="sample-row" data-label="{label}">'
                '<td style="font-weight:600;color:#6366f1">{label}</td>'
                '<td colspan="9" style="color:#dc2626;font-size:12px">Error: {error}</td>'
                '</tr>'.format(label=s["label"], error=error_msg)
            )
            continue
        sm = s["summary"]
        flagged = sm["n_flagged"]
        flag_badge = (
            '<span style="background:#fef2f2;color:#dc2626;border:1px solid #fca5a5;'
            'border-radius:4px;padding:1px 6px;font-size:11px">{n} flagged</span>'.format(n=flagged)
            if flagged else ""
        )
        metric_cells = "".join('<td>{b}</td>'.format(b=bar(sm["mean_" + m])) for m in METRICS)

        q_header_cells = "".join(
            '<th style="padding:6px 8px">{l}</th>'.format(l=l) for l in LABELS
        )
        q_rows = build_question_rows(s["question_evaluations"])
        desc = s["description"][:120] + ("..." if len(s["description"]) > 120 else "")

        code_escaped = escape_html(s.get("code", ""))
        label = s["label"]
        code_section = (
            '<div style="margin-bottom:16px">'
            '<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
            '<span style="font-size:13px;font-weight:600;color:#374151">Source Code</span>'
            '<button onclick="toggleCode(\'{label}\')" id="codebtn-{label}" '
            'style="background:#e0e7ff;color:#4338ca;border:none;border-radius:4px;'
            'padding:2px 8px;cursor:pointer;font-size:11px">Show</button>'
            '</div>'
            '<pre id="code-{label}" style="display:none;background:#1e293b;color:#e2e8f0;'
            'border-radius:8px;padding:16px;font-size:12px;overflow-x:auto;'
            'line-height:1.6;margin:0;white-space:pre">{code}</pre>'
            '</div>'
        ).format(label=label, code=code_escaped)

        parts.append(
            '<tr class="sample-row" data-label="{label}">'
            '<td style="font-weight:600;color:#6366f1">{label}</td>'
            '<td style="max-width:340px;font-size:12px;color:#6b7280">{desc}</td>'
            '<td style="text-align:center">{nq}</td>'
            '{metrics}'
            '<td>{overall}</td>'
            '<td>{flags}</td>'
            '<td><button onclick="toggleDetails(\'{label}\')" style="background:#e0e7ff;color:#4338ca;border:none;border-radius:4px;padding:4px 10px;cursor:pointer;font-size:12px">Details</button></td>'
            '</tr>'
            '<tr id="details-{label}" style="display:none">'
            '<td colspan="10" style="background:#f8fafc;padding:16px">'
            '{code_section}'
            '<div style="font-size:13px;font-weight:600;margin-bottom:8px;color:#374151">Question Evaluations</div>'
            '<table style="width:100%;border-collapse:collapse;font-size:12px">'
            '<tr style="background:#f1f5f9">'
            '<th style="padding:6px 8px;text-align:left">Q#</th>'
            '<th style="padding:6px 8px;text-align:left;max-width:300px">Question</th>'
            '{q_header}'
            '<th style="padding:6px 8px">Overall</th>'
            '<th style="padding:6px 8px">Flagged</th>'
            '</tr>'
            '{q_rows}'
            '</table>'
            '</td>'
            '</tr>'.format(
                label=label,
                desc=desc,
                nq=sm["n_questions"],
                metrics=metric_cells,
                overall=bar(sm["mean_overall"]),
                flags=flag_badge,
                code_section=code_section,
                q_header=q_header_cells,
                q_rows=q_rows,
            )
        )
    return "".join(parts)


rows_html = build_sample_rows(samples)
col_headers = "".join('<th>{l}</th>'.format(l=l) for l in LABELS)

chart_labels = json.dumps([s["label"] for s in samples])
chart_overall = json.dumps([s["summary"]["mean_overall"] if "summary" in s else None for s in samples])

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>QLC Batch Evaluation Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: #f8fafc; color: #1e293b; }}
  h1 {{ margin: 0; font-size: 22px; }}
  .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 24px 32px; }}
  .header p {{ margin: 4px 0 0; opacity: 0.85; font-size: 14px; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 24px 32px; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 28px; }}
  .card {{ background: white; border-radius: 10px; padding: 18px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.07); }}
  .card .val {{ font-size: 28px; font-weight: 700; margin: 4px 0 2px; }}
  .card .lbl {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: .5px; }}
  table.main {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.07); font-size: 13px; }}
  table.main th {{ background: #f1f5f9; padding: 10px 12px; text-align: left; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: .4px; white-space: nowrap; }}
  table.main td {{ padding: 10px 12px; border-top: 1px solid #f1f5f9; vertical-align: middle; }}
  table.main tr.sample-row:hover {{ background: #fafafa; }}
  .search {{ margin-bottom: 16px; display:flex; gap:12px; align-items:center; }}
  .search input {{ padding: 8px 14px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 13px; width: 300px; outline:none; }}
  .search input:focus {{ border-color: #6366f1; }}
  .chart-wrap {{ background: white; border-radius: 10px; padding: 20px 24px; box-shadow: 0 1px 4px rgba(0,0,0,.07); margin-bottom: 28px; }}
  .chart-wrap h2 {{ margin: 0 0 16px; font-size: 15px; color: #374151; }}
  canvas {{ max-height: 260px; }}
</style>
</head>
<body>
<div class="header">
  <h1>QLC Batch Evaluation Report</h1>
  <p>Run: {timestamp} &nbsp;|&nbsp; {n_total} questions across {n_samples} samples</p>
</div>
<div class="container">
  <div class="cards">
    <div class="card"><div class="lbl">Total Questions</div><div class="val" style="color:#6366f1">{n_total}</div></div>
    <div class="card"><div class="lbl">Overall Score</div><div class="val" style="color:{oc}">{mean_overall}</div><div style="font-size:11px;color:#9ca3af">/ 5.00</div></div>
    <div class="card"><div class="lbl">Accuracy</div><div class="val" style="color:{acc}">{mean_accuracy}</div></div>
    <div class="card"><div class="lbl">Clarity</div><div class="val" style="color:{cla}">{mean_clarity}</div></div>
    <div class="card"><div class="lbl">Pedagogical Value</div><div class="val" style="color:{pv}">{mean_pv}</div></div>
    <div class="card"><div class="lbl">Code Specificity</div><div class="val" style="color:{cs}">{mean_cs}</div></div>
    <div class="card"><div class="lbl">Difficulty Calib.</div><div class="val" style="color:{dc}">{mean_dc}</div></div>
    <div class="card"><div class="lbl">Flagged</div><div class="val" style="color:#dc2626">{n_flagged}</div><div style="font-size:11px;color:#9ca3af">{flag_pct}% of questions</div></div>
  </div>
  <div class="chart-wrap">
    <h2>Per-Sample Overall Score</h2>
    <canvas id="chart"></canvas>
  </div>
  <div class="search">
    <input id="searchInput" type="text" placeholder="Filter by label or description..." oninput="filterTable()">
    <span style="font-size:13px;color:#6b7280" id="countLabel">{n_samples} samples</span>
  </div>
  <table class="main" id="mainTable">
    <thead>
      <tr>
        <th>Label</th><th>Description</th><th>Qs</th>
        {col_headers}
        <th>Overall</th><th>Flags</th><th></th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<script>
const labels = {chart_labels};
const overall = {chart_overall};
new Chart(document.getElementById('chart'), {{
  type: 'bar',
  data: {{
    labels: labels,
    datasets: [{{
      label: 'Mean Overall Score',
      data: overall,
      backgroundColor: overall.map(v => v >= 4.5 ? '#86efac' : v >= 3.5 ? '#fde047' : '#fca5a5'),
      borderColor: overall.map(v => v >= 4.5 ? '#22c55e' : v >= 3.5 ? '#eab308' : '#ef4444'),
      borderWidth: 1, borderRadius: 3,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: ctx => ` Score: ${{ctx.raw.toFixed(2)}}` }} }} }},
    scales: {{
      y: {{ min: 0, max: 5, grid: {{ color: '#f1f5f9' }} }},
      x: {{ ticks: {{ maxRotation: 45, font: {{ size: 10 }} }}, grid: {{ display: false }} }}
    }}
  }}
}});
function toggleDetails(label) {{
  const row = document.getElementById('details-' + label);
  row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
}}
function toggleCode(label) {{
  const pre = document.getElementById('code-' + label);
  const btn = document.getElementById('codebtn-' + label);
  const visible = pre.style.display !== 'none';
  pre.style.display = visible ? 'none' : 'block';
  btn.textContent = visible ? 'Show' : 'Hide';
}}
function filterTable() {{
  const q = document.getElementById('searchInput').value.toLowerCase();
  const rows = document.querySelectorAll('tr.sample-row');
  let visible = 0;
  rows.forEach(row => {{
    const show = !q || row.dataset.label.toLowerCase().includes(q) || row.cells[1].textContent.toLowerCase().includes(q);
    row.style.display = show ? '' : 'none';
    const det = document.getElementById('details-' + row.dataset.label);
    if (!show && det) det.style.display = 'none';
    if (show) visible++;
  }});
  document.getElementById('countLabel').textContent = visible + ' samples';
}}
</script>
</body>
</html>""".format(
    timestamp=data["run_timestamp"],
    n_total=g["n_total_questions"],
    n_samples=len(samples),
    oc=score_color(g["mean_overall"]),
    mean_overall="{:.2f}".format(g["mean_overall"]),
    acc=score_color(g["mean_accuracy"]),
    mean_accuracy="{:.2f}".format(g["mean_accuracy"]),
    cla=score_color(g["mean_clarity"]),
    mean_clarity="{:.2f}".format(g["mean_clarity"]),
    pv=score_color(g["mean_pedagogical_value"]),
    mean_pv="{:.2f}".format(g["mean_pedagogical_value"]),
    cs=score_color(g["mean_code_specificity"]),
    mean_cs="{:.2f}".format(g["mean_code_specificity"]),
    dc=score_color(g["mean_difficulty_calibration"]),
    mean_dc="{:.2f}".format(g["mean_difficulty_calibration"]),
    n_flagged=g["n_flagged"],
    flag_pct="{:.1f}".format(g["n_flagged"] / g["n_total_questions"] * 100),
    col_headers=col_headers,
    rows=rows_html,
    chart_labels=chart_labels,
    chart_overall=chart_overall,
)

OUTPUT.write_text(html)
print("Report written to: {}".format(OUTPUT))
print("Open with: xdg-open {}  (or open in browser)".format(OUTPUT))
