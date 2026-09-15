#!/usr/bin/env python3
"""
build_dashboard.py
==================
MBAX 6418 — Assignment 1, Steps 3 & 4.
Builds a polished, fully self-contained HTML dashboard from the Step 2 CSV
results. The data is embedded directly into the HTML, so the file works fully
offline when opened directly in a browser (no server, no network).

Reads    : results/step2_predictions.csv
Writes   : dashboard.html
Prints   : the computed statistics (for verification against the CSV).
"""
import csv
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CSV_PATH = ROOT / "results" / "step2_predictions.csv"
OUT_PATH = ROOT / "dashboard.html"


# ---------------------------------------------------------------------------
# 1. Read + compute stats (also used for the printed verification)
# ---------------------------------------------------------------------------
def load_rows():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_stats(rows):
    total = len(rows)
    n_correct = sum(1 for r in rows if r["correct"] == "True")
    n_incorrect = total - n_correct
    accuracy = n_correct / total if total else 0.0

    actual = {"POSITIVE": 0, "NEGATIVE": 0}
    pred = {"POSITIVE": 0, "NEGATIVE": 0}
    for r in rows:
        actual[r["actual_sentiment"]] += 1
        pred[r["predicted_sentiment"]] += 1

    cm = {}
    for a in ("POSITIVE", "NEGATIVE"):
        for p in ("POSITIVE", "NEGATIVE"):
            cm[(a, p)] = sum(1 for r in rows
                             if r["actual_sentiment"] == a
                             and r["predicted_sentiment"] == p)

    def cls_acc(cls):
        tot = actual[cls]
        right = cm[(cls, cls)]
        return (right / tot if tot else 0.0), tot

    pos_acc, pos_tot = cls_acc("POSITIVE")
    neg_acc, neg_tot = cls_acc("NEGATIVE")
    return {
        "total": total, "n_correct": n_correct, "n_incorrect": n_incorrect,
        "accuracy": accuracy, "actual": actual, "pred": pred,
        "cm": cm,
        "pos_acc": pos_acc, "pos_tot": pos_tot,
        "neg_acc": neg_acc, "neg_tot": neg_tot,
    }


def emit_data(rows):
    """Return a JSON string of compact review records safe to embed in HTML."""
    compact = [
        {
            "i": int(r["index"]),
            "r": float(r["rating"]),
            "t": r["title"],
            "x": r["text"],
            "a": r["actual_sentiment"],
            "p": r["predicted_sentiment"],
            "c": r["correct"] == "True",
        }
        for r in rows
    ]
    data = json.dumps(compact, ensure_ascii=False)
    return data.replace("</", "<\\/")  # never break out of the <script> tag


# ---------------------------------------------------------------------------
# 2. HTML template
# ---------------------------------------------------------------------------
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MBAX 6418 · Sentiment Classification Dashboard</title>
<style>
  :root{
    --bg:#f4f5fa; --card:#ffffff; --text:#1a1d29; --muted:#697386;
    --line:#e6e8f0; --accent:#4f46e5; --accent-soft:#eef0ff;
    --pos:#0e9f6e; --pos-soft:#e5f7f0;
    --neg:#e11d48; --neg-soft:#fee9ee;
    --warn:#d97706; --ok:#16a34a; --bad:#dc2626;
    --r:16px; --shadow:0 1px 2px rgba(20,24,45,.05), 0 8px 24px -12px rgba(20,24,45,.12);
  }
  *{box-sizing:border-box; margin:0; padding:0}
  body{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Helvetica,Arial,sans-serif;
    background:var(--bg); color:var(--text); line-height:1.5;
    -webkit-font-smoothing:antialiased; padding:32px 20px 64px;
  }
  .wrap{max-width:1180px; margin:0 auto}
  .head{display:flex; align-items:flex-end; justify-content:space-between;
        flex-wrap:wrap; gap:12px; margin-bottom:26px}
  .eyebrow{font-size:12px; letter-spacing:.08em; text-transform:uppercase;
           color:var(--accent); font-weight:700; margin-bottom:6px}
  h1{font-size:26px; font-weight:750; letter-spacing:-.02em}
  .sub{color:var(--muted); font-size:14px; margin-top:6px}
  .badge{background:var(--accent-soft); color:var(--accent); font-weight:700;
         border-radius:999px; padding:6px 14px; font-size:13px}

  /* ---- Metric cards ---- */
  .grid{display:grid; gap:16px}
  .kpis{grid-template-columns:repeat(6,1fr); margin-bottom:16px}
  .card{background:var(--card); border:1px solid var(--line); border-radius:var(--r);
        box-shadow:var(--shadow); padding:18px 20px}
  .kpi .label{font-size:12px; color:var(--muted); font-weight:600;
              text-transform:uppercase; letter-spacing:.05em}
  .kpi .num{font-size:30px; font-weight:800; letter-spacing:-.02em; margin-top:6px}
  .kpi .foot{font-size:12px; color:var(--muted); margin-top:4px}
  .kpi.accent .num{color:var(--accent)}
  .kpi.pos .num{color:var(--pos)} .kpi.neg .num{color:var(--neg)}
  .kpi.ok .num{color:var(--ok)} .kpi.bad .num{color:var(--bad)}

  .row2{grid-template-columns:1.05fr 1.05fr 1.4fr; margin-bottom:16px}
  .panel h3{font-size:15px; font-weight:700; margin-bottom:16px;
            display:flex; align-items:center; gap:8px; letter-spacing:-.01em}
  .panel h3 .dot{width:9px;height:9px;border-radius:2px}

  /* ---- Confusion matrix ---- */
  .cm{display:grid; grid-template-columns:auto 1fr 1fr; gap:8px; align-items:stretch}
  .cm .corner{color:var(--muted); font-size:12px; font-weight:700;
              display:flex; align-items:flex-end; justify-content:flex-end;
              padding:0 4px 6px 0}
  .cm .clab{font-size:12px; font-weight:700; color:var(--muted);
            display:flex; align-items:center; padding-right:8px}
  .cm .cell{border:1px solid var(--line); border-radius:10px; padding:10px 12px;
            text-align:left; min-width:90px}
  .cm .cell b{font-size:22px; font-weight:800; display:block; letter-spacing:-.02em}
  .cm .cell span{font-size:11px; color:var(--muted); font-weight:600}
  .cm .pp{background:var(--pos-soft); border-color:#bfe6d5}
  .cm .nn{background:var(--neg-soft); border-color:#f6c6d1}
  .cm .pn{background:#fef3e8; border-color:#f7dcb8}
  .cm .np{background:#fef3e8; border-color:#f7dcb8}
  .cm .cm-act{font-size:11px; color:var(--muted); font-weight:600;
              grid-column:2/4; text-align:center; padding-top:2px}

  /* ---- Distribution bars ---- */
  .bars{display:flex; flex-direction:column; gap:16px}
  .bar-group .bhead{display:flex; justify-content:space-between; font-size:12px;
                     color:var(--muted); font-weight:600; margin-bottom:6px}
  .bar-wrapper{position:relative; height:30px; background:#f1f2f8;
               border-radius:8px; overflow:hidden}
  .bar-inner{height:100%; border-radius:8px; display:flex; align-items:center;
             padding-left:10px; color:#fff; font-weight:700; font-size:12px;
             transition:width .6s cubic-bezier(.2,.8,.2,1); white-space:nowrap}
  .legend{display:flex; gap:18px; font-size:12px; color:var(--muted); margin-top:12px}
  .legend i{width:10px;height:10px;border-radius:3px;display:inline-block;margin-right:6px;vertical-align:-1px}

  /* ---- Class accuracy ---- */
  .acc{display:flex; flex-direction:column; gap:16px}
  .acc-row .ar-head{display:flex; justify-content:space-between; font-size:13px;
                     font-weight:600; margin-bottom:6px}
  .acc-row .ar-head small{color:var(--muted); font-weight:500}
  .track{height:10px; background:#eef0f7; border-radius:99px; overflow:hidden}
  .fill{height:100%; border-radius:99px}

  /* ---- Table ---- */
  .table-card{padding:0; overflow:hidden}
  .table-toolbar{display:flex; flex-wrap:wrap; gap:14px; align-items:center;
                 justify-content:space-between; padding:18px 22px;
                 border-bottom:1px solid var(--line)}
  .filters{display:flex; flex-wrap:wrap; gap:10px; align-items:center}
  .seg{display:inline-flex; background:#eef0f7; border-radius:10px; padding:3px; gap:2px}
  .seg button{border:0; background:transparent; padding:7px 14px; border-radius:8px;
              font-size:13px; font-weight:600; color:var(--muted); cursor:pointer;
              transition:all .15s}
  .seg button.active{background:#fff; color:var(--text); box-shadow:var(--shadow)}
  select{font-family:inherit; font-size:13px; padding:8px 10px; border:1px solid var(--line);
         border-radius:9px; background:#fff; color:var(--text); cursor:pointer; font-weight:600}
  .search{flex:1; min-width:200px}
  .search input{width:100%; font-family:inherit; font-size:13px; padding:9px 12px;
                border:1px solid var(--line); border-radius:9px; background:#fff;
                color:var(--text); outline:none}
  .search input:focus{border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-soft)}
  .count-line{padding:12px 22px; font-size:13px; color:var(--muted);
              border-bottom:1px solid var(--line); background:#fafbfe;
              display:flex; justify-content:space-between; align-items:center}
  .count-line b{color:var(--text)}
  .scroll{overflow:auto; max-height:560px}
  table{width:100%; border-collapse:collapse; font-size:13px}
  thead th{position:sticky; top:0; background:#fafbfe; text-align:left; z-index:2;
           color:var(--muted); font-size:11px; text-transform:uppercase;
           letter-spacing:.06em; padding:10px 22px; border-bottom:1px solid var(--line);
           cursor:pointer; user-select:none; white-space:nowrap}
  thead th:hover{color:var(--accent)}
  tbody td{padding:12px 22px; border-bottom:1px solid #f0f1f7; vertical-align:top}
  tbody tr:hover{background:#fafbff}
  td.rt{width:74px; font-weight:700; color:#333a4d}
  .stars{color:var(--warn); letter-spacing:1px}
  td.big{max-width:400px}
  .title{font-weight:700; color:#23293c}
  .txt{color:var(--muted); margin-top:3px; display:block}
  .pill{display:inline-block; padding:3px 10px; border-radius:999px; font-size:11px;
        font-weight:700; letter-spacing:.02em}
  .pill.pos{background:var(--pos-soft); color:var(--pos)}
  .pill.neg{background:var(--neg-soft); color:var(--neg)}
  .pill.ok{background:#e7f6ec; color:var(--ok)}
  .pill.bad{background:#fdecef; color:var(--bad)}
  .state{font-weight:700}
  .state.ok{color:var(--ok)} .state.bad{color:var(--bad)}
  .empty{padding:40px; text-align:center; color:var(--muted)}
  th .arrow{opacity:.5; font-size:10px; margin-left:2px}
  footer{margin-top:22px; color:var(--muted); font-size:12px; text-align:center}
  @media (max-width:1024px){ .kpis{grid-template-columns:repeat(3,1fr)}
                             .row2{grid-template-columns:1fr} }
  @media (max-width:560px){ .kpis{grid-template-columns:repeat(2,1fr)} }
</style>
</head>
<body>
<div class="wrap">

  <div class="head">
    <div>
      <div class="eyebrow">MBAX 6418 · Assignment 1</div>
      <h1>Review Sentiment — Classification Dashboard</h1>
      <div class="sub" id="sub">First 100 Amazon Gift Card reviews · LLM: DeepSeek-V4-Flash-0731 (temperature 0.0) · rating never sent to model</div>
    </div>
    <div class="badge">Binary · POS / NEG</div>
  </div>

  <!-- KPI cards -->
  <div class="grid kpis" id="kpis"></div>

  <div class="grid row2">
    <!-- Confusion matrix -->
    <div class="card panel">
      <h3><span class="dot" style="background:var(--accent)"></span>Confusion matrix</h3>
      <div class="cm" id="cm"></div>
    </div>
    <!-- Distribution -->
    <div class="card panel">
      <h3><span class="dot" style="background:#0ea5e9"></span>Actual vs predicted</h3>
      <div class="bars" id="bars"></div>
      <div class="legend">
        <span><i style="background:#9aa3b8"></i>Actual</span>
        <span><i style="background:var(--accent)"></i>Predicted</span>
      </div>
    </div>
    <!-- Class accuracy -->
    <div class="card panel">
      <h3><span class="dot" style="background:#0e9f6e"></span>Class-level accuracy</h3>
      <div class="acc" id="acc"></div>
    </div>
  </div>

  <!-- Review table -->
  <div class="card table-card">
    <div class="table-toolbar">
      <div class="filters">
        <div class="seg" id="statusSeg">
          <button data-v="all" class="active">All</button>
          <button data-v="correct">Correct</button>
          <button data-v="mismatch">Mismatched</button>
        </div>
        <select id="actualFilt" title="Filter by actual class">
          <option value="all">Any actual class</option>
          <option value="POSITIVE">Actual: POSITIVE</option>
          <option value="NEGATIVE">Actual: NEGATIVE</option>
        </select>
        <select id="predFilt" title="Filter by predicted class">
          <option value="all">Any predicted class</option>
          <option value="POSITIVE">Predicted: POSITIVE</option>
          <option value="NEGATIVE">Predicted: NEGATIVE</option>
        </select>
      </div>
      <div class="search">
        <input id="search" type="text" placeholder="Search title or review text…">
      </div>
    </div>

    <div class="count-line">
      <span>Showing <b id="visibleCount">0</b> of <b id="totalCount">0</b> reviews</span>
      <span id="filterDesc" style="color:#9aa3b8"></span>
    </div>

    <div class="scroll">
      <table>
        <thead>
          <tr>
            <th data-k="r">Rating</th>
            <th data-k="t">Title / Review</th>
            <th data-k="a">Actual</th>
            <th data-k="p">Predicted</th>
            <th data-k="s">Status</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>

  <footer>Built automatically from <code>results/step2_predictions.csv</code> · filters update the visible count live · data embedded, works offline</footer>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById("data").textContent);
const POS="POSITIVE", NEG="NEGATIVE";

/* ---------- helpers ---------- */
const stars = n => { const c=Math.round(n); return "★".repeat(c)+"☆".repeat(5-c); };
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct = (num,den) => den? (100*num/den).toFixed(1)+"%" : "—";
function fill(color,w,label){ w=Math.max(Number(w)||0,3); const show=(label&&w>=40)?label:"";
  return `<div class="bar-wrapper"><div class="bar-inner" style="width:${w}%;background:${color}">${show}</div></div>`; }

/* ---------- stats ---------- */
const S = (()=>{
  const total=DATA.length;
  const n_correct=DATA.filter(d=>d.c).length, n_incorrect=total-n_correct;
  const actual={POSITIVE:0,NEGATIVE:0}, pred={POSITIVE:0,NEGATIVE:0}, cm={PP:0,PN:0,NP:0,NN:0};
  for(const d of DATA){
    actual[d.a]++; pred[d.p]++;
    if(d.a===POS) d.p===POS?cm.PP++:cm.PN++; else d.p===POS?cm.NP++:cm.NN++;
  }
  const cls=(c)=> actual[c]? (cm[c==POS?"PP":"NN"]/actual[c]) : 0;
  return {total,n_correct,n_incorrect,acc:n_correct/total,actual,pred,cm,
          posAcc:cls(POS),negAcc:cls(NEG),max:Math.max(actual.POSITIVE,actual.NEGATIVE,pred.POSITIVE,pred.NEGATIVE)};
})();

/* ---------- render KPIs ---------- */
const kpis=[
 {c:"accent",l:"Total reviews",n:S.total,f:"first 100 of dataset"},
 {c:"ok",l:"Correct",n:S.n_correct,f:pct(S.n_correct,S.total)+" overall accuracy"},
 {c:"bad",l:"Incorrect",n:S.n_incorrect,f:"mismatches"},
 {c:"pos",l:"Actual POSITIVE",n:S.actual.POSITIVE,f:"rating ≥ 4"},
 {c:"neg",l:"Actual NEGATIVE",n:S.actual.NEGATIVE,f:"rating < 4"},
 {c:"accent",l:"Overall accuracy",n:pct(S.n_correct,S.total),f:S.n_correct+"/"+S.total},
];
document.getElementById("kpis").innerHTML = kpis.map(k=>
  `<div class="card kpi ${k.c}"><div class="label">${k.l}</div><div class="num">${k.n}</div><div class="foot">${k.f}</div></div>`).join("");

/* ---------- confusion matrix ---------- */
const cmSpec={PP:["POSITIVE → POSITIVE","var(--pos)"],PN:["POSITIVE → NEGATIVE","var(--warn)"],
              NP:["NEGATIVE → POSITIVE","var(--warn)"],NN:["NEGATIVE → NEGATIVE","var(--neg)"]};
let cmHTML=`<div class="corner">predicted →</div><div class="cm-head" style="text-align:center;font-size:12px;font-weight:700;color:var(--muted)">POSITIVE</div><div style="text-align:center;font-size:12px;font-weight:700;color:var(--muted)">NEGATIVE</div>
<div class="clab">actual↓<br>POSITIVE</div><div class="cell pp"><b>${S.cm.PP}</b><span>${cmSpec.PP[0]}</span></div><div class="cell pn"><b>${S.cm.PN}</b><span>${cmSpec.PN[0]}</span></div>
<div class="clab">NEGATIVE</div><div class="cell np"><b>${S.cm.NP}</b><span>${cmSpec.NP[0]}</span></div><div class="cell nn"><b>${S.cm.NN}</b><span>${cmSpec.NN[0]}</span></div>`;
document.getElementById("cm").innerHTML=cmHTML;

/* ---------- distribution bars ---------- */
document.getElementById("bars").innerHTML =
 `<div class="bar-group"><div class="bhead"><span>POSITIVE</span><span>${S.actual.POSITIVE} actual · ${S.pred.POSITIVE} predicted</span></div>
   ${fill("#9aa3b8", 100*S.actual.POSITIVE/S.max, "Actual "+S.actual.POSITIVE)}
   <div style="height:8px"></div>
   ${fill("var(--accent)", 100*S.pred.POSITIVE/S.max, "Predicted "+S.pred.POSITIVE)}</div>
  <div class="bar-group"><div class="bhead"><span>NEGATIVE</span><span>${S.actual.NEGATIVE} actual · ${S.pred.NEGATIVE} predicted</span></div>
   ${fill("#9aa3b8", 100*S.actual.NEGATIVE/S.max, "Actual "+S.actual.NEGATIVE)}
   <div style="height:8px"></div>
   ${fill("var(--accent)", 100*S.pred.NEGATIVE/S.max, "Predicted "+S.pred.NEGATIVE)}</div>`;

/* ---------- class accuracy ---------- */
const accRow=(label,val,tot,color)=>`
 <div class="acc-row"><div class="ar-head"><span>${label} <small>· ${tot} reviews</small></span><span>${(100*val).toFixed(1)}%</span></div>
 <div class="track"><div class="fill" style="width:${100*val}%;background:${color}"></div></div></div>`;
document.getElementById("acc").innerHTML=
  accRow("POSITIVE",S.posAcc,S.actual.POSITIVE,"var(--pos)")+
  accRow("NEGATIVE",S.negAcc,S.actual.NEGATIVE,"var(--neg)")+
  accRow("Overall",S.acc,S.total,"var(--accent)");

/* ---------- table + filters ---------- */
let state={status:"all",actual:"all",pred:"all",q:"",sort:"r",dir:-1};
const statusEls=document.querySelectorAll(".seg button");

function visible(){
  const q=state.q.toLowerCase();
  return DATA.filter(d=>{
    if(state.status==="correct"&&!d.c) return false;
    if(state.status==="mismatch"&&d.c) return false;
    if(state.actual!=="all"&&d.a!==state.actual) return false;
    if(state.pred!=="all"&&d.p!==state.pred) return false;
    if(q && !(d.t.toLowerCase().includes(q)||d.x.toLowerCase().includes(q))) return false;
    return true;
  });
}
function render(){
  let list=visible();
  const dir=state.dir, k=state.sort;
  list.sort((a,b)=>{ const av=k==="r"?a.r:(a[k]||""), bv=k==="r"?b.r:(b[k]||""); 
    let c; if(typeof av==="number"&&typeof bv==="number") c=av-bv; else c=String(av).localeCompare(String(bv)); return c*dir; });
  document.getElementById("tbody").innerHTML=list.length? list.map(d=>`
   <tr>
    <td class="rt">${d.r.toFixed(1)}<div class="stars">${stars(d.r)}</div></td>
    <td class="big"><div class="title">${esc(d.t)}</div><span class="txt">${esc(d.x)}</span></td>
    <td><span class="pill ${d.a===POS?'pos':'neg'}">${d.a}</span></td>
    <td><span class="pill ${d.p===POS?'pos':'neg'}">${d.p}</span></td>
    <td><span class="state ${d.c?'ok':'bad'}">${d.c?'✓ Correct':'✗ Mismatch'}</span></td>
   </tr>`).join("") : `<tr><td colspan="5"><div class="empty">No reviews match the current filters.</div></td></tr>`;
  document.getElementById("visibleCount").textContent=list.length;
  document.getElementById("totalCount").textContent=S.total;
  const parts=[]; if(state.status!=="all")parts.push(state.status);
  if(state.actual!=="all")parts.push("actual="+state.actual);
  if(state.pred!=="all")parts.push("predicted="+state.pred);
  document.getElementById("filterDesc").textContent=parts.length? "filtered: "+parts.join(", "):"";
}
/* events */
document.getElementById("statusSeg").addEventListener("click",e=>{
  const b=e.target.closest("button"); if(!b)return;
  statusEls.forEach(x=>x.classList.remove("active")); b.classList.add("active"); state.status=b.dataset.v; render();
});
["actualFilt","predFilt"].forEach(id=>document.getElementById(id).addEventListener("change",e=>{
  state[id==="actualFilt"?"actual":"pred"]=e.target.value; render(); }));
document.getElementById("search").addEventListener("input",e=>{state.q=e.target.value;render();});
document.querySelectorAll("thead th").forEach(th=>th.addEventListener("click",()=>{
  const k=th.dataset.k; if(state.sort===k) state.dir*=-1; else {state.sort=k;state.dir= k==="r"?-1:1;} render(); }));

render();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# 3. Build + write + verify
# ---------------------------------------------------------------------------
def main():
    rows = load_rows()
    stats = compute_stats(rows)

    html = HTML.replace("__DATA__", emit_data(rows))
    OUT_PATH.write_text(html, encoding="utf-8")

    print("Dashboard written:", OUT_PATH)
    print(f"size: {OUT_PATH.stat().st_size/1024:.1f} KB  |  rows embedded: {len(rows)}")
    print("\n--- VERIFICATION (computed from CSV at build time) ---")
    print(f"total={stats['total']}  correct={stats['n_correct']}  incorrect={stats['n_incorrect']}")
    print(f"overall accuracy={stats['accuracy']*100:.2f}%")
    print(f"actual POS/NEG = {stats['actual']['POSITIVE']}/{stats['actual']['NEGATIVE']}")
    print(f"predicted POS/NEG = {stats['pred']['POSITIVE']}/{stats['pred']['NEGATIVE']}")
    print(f"confusion PP/PN / NP/NN = {stats['cm'][('POSITIVE','POSITIVE')]}/{stats['cm'][('POSITIVE','NEGATIVE')]} / "
          f"{stats['cm'][('NEGATIVE','POSITIVE')]}/{stats['cm'][('NEGATIVE','NEGATIVE')]}")
    print(f"positive accuracy={stats['pos_acc']*100:.2f}% ({stats['cm'][('POSITIVE','POSITIVE')]}/{stats['pos_tot']})")
    print(f"negative accuracy={stats['neg_acc']*100:.2f}% ({stats['cm'][('NEGATIVE','NEGATIVE')]}/{stats['neg_tot']})")
    print("compressed data size:", len(emit_data(rows)), "chars")


if __name__ == "__main__":
    main()
