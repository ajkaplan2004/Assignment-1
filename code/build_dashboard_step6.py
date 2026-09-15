#!/usr/bin/env python3
"""
build_dashboard_step6.py
========================
MBAX 6418 — Assignment 1, Step 6.
Builds a polished, fully self-contained HTML dashboard from the balanced
three-class run (data/step6_balanced_results.csv). All statistics are computed
client-side from the embedded data, so every displayed number matches the CSV
by construction; the script also computes the same stats in Python and prints
them for independent verification.

Output: dashboard_step6.html  (works fully offline)
"""
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CSV_PATH = ROOT / "data" / "step6_balanced_results.csv"
OUT_PATH = ROOT / "dashboard_step6.html"

CLASSES = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
EMOTIONS = ["anger", "anticipation", "disgust", "fear",
            "joy", "sadness", "surprise", "trust"]


# ---------------------------------------------------------------------------
# Read + compute (for build-time verification)
# ---------------------------------------------------------------------------
def load_rows():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_stats(rows):
    total = len(rows)
    n_correct = sum(1 for r in rows if r["correct"] == "True")

    def cls_acc(c):
        sub = [r for r in rows if r["actual_sentiment"] == c]
        ok = sum(1 for r in sub if r["predicted_sentiment"] == c)
        return round(ok / len(sub), 4) if sub else None

    cm = {f"{a}-{p}": sum(1 for r in rows if r["actual_sentiment"] == a
                          and r["predicted_sentiment"] == p)
          for a in CLASSES for p in CLASSES}

    stars = {}
    for s in range(1, 6):
        stars[str(s)] = sum(1 for r in rows if int(round(float(r["rating"]))) == s)

    llm_dist = {}
    nrc_dist = {}
    for e in EMOTIONS:
        llm_dist[e] = sum(1 for r in rows if r["llm_emotion"] == e)
        nrc_dist[e] = sum(1 for r in rows if r["nrc_emotion"] == e)
    llm_dist["none"] = sum(1 for r in rows if not r["llm_emotion"])
    nrc_dist["none"] = sum(1 for r in rows if not r["nrc_emotion"])

    both = [r for r in rows if r["llm_emotion"] and r["nrc_emotion"]]
    emo_agree = sum(1 for r in both if r["llm_emotion"] == r["nrc_emotion"])

    return {
        "total": total, "n_correct": n_correct,
        "overall": round(n_correct / total, 4),
        "per": {c: cls_acc(c) for c in CLASSES},
        "cm": cm, "stars": stars,
        "llm_dist": llm_dist, "nrc_dist": nrc_dist,
        "emo_agree": emo_agree, "emo_both": len(both),
        "actual": {c: sum(1 for r in rows if r["actual_sentiment"] == c) for c in CLASSES},
        "pred": {c: sum(1 for r in rows if r["predicted_sentiment"] == c) for c in CLASSES},
    }


def emit_data(rows):
    compact = [
        {"i": int(r["index"]), "r": float(r["rating"]), "t": r["title"], "x": r["text"],
         "a": r["actual_sentiment"], "p": r["predicted_sentiment"],
         "c": r["correct"] == "True",
         "le": r["llm_emotion"], "ne": r["nrc_emotion"]}
        for r in rows
    ]
    return json.dumps(compact, ensure_ascii=False).replace("</", "<\\/")


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MBAX 6418 · 3-Class Sentiment Dashboard</title>
<style>
  :root{
    --bg:#f4f6fa; --card:#ffffff; --ink:#0f172a; --muted:#5b6472; --faint:#94a3b8;
    --line:#e6e9f0; --accent:#4f46e5; --accent-soft:#eef0ff;
    --pos:#0e9f6e; --pos-soft:#e3f6ee;
    --neu:#d97706; --neu-soft:#fdf0da;
    --neg:#dc2626; --neg-soft:#fdecee;
    --brand:#1e293b;
    --r:14px; --shadow:0 1px 2px rgba(15,23,42,.05), 0 10px 28px -14px rgba(15,23,42,.16);
  }
  *{box-sizing:border-box; margin:0; padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Helvetica,Arial,sans-serif;
    background:var(--bg); color:var(--ink); line-height:1.5; -webkit-font-smoothing:antialiased;
    padding:0 0 72px}
  .top{background:linear-gradient(135deg,#1e293b 0%,#334155 60%,#4f46e5 130%); color:#e2e8f0; padding:30px 28px 26px}
  .wrap{max-width:1240px; margin:0 auto}
  .eyebrow{font-size:12px; letter-spacing:.1em; text-transform:uppercase; color:#a5b4fc; font-weight:700}
  h1{color:#fff; font-size:26px; font-weight:800; letter-spacing:-.02em; margin-top:6px}
  .sub{color:#cbd5e1; font-size:14px; margin-top:8px; max-width:820px}
  .chips{display:flex; flex-wrap:wrap; gap:8px; margin-top:14px}
  .chip{background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.15); color:#f1f5f9;
    padding:5px 12px; border-radius:999px; font-size:12px; font-weight:600}

  .wrap{ }
  .section{max-width:1240px; margin:0 auto; padding:0 28px}
  .grid{display:grid; gap:16px}
  .kpis{grid-template-columns:repeat(6,1fr); margin-top:20px}
  .card{background:var(--card); border:1px solid var(--line); border-radius:var(--r); box-shadow:var(--shadow); padding:18px 20px}
  .kpi{padding:16px 18px; display:flex; flex-direction:column; justify-content:space-between; min-height:104px}
  .kpi .lab{font-size:11px; letter-spacing:.07em; text-transform:uppercase; color:var(--muted); font-weight:700}
  .kpi .num{font-size:32px; font-weight:800; letter-spacing:-.03em; margin-top:6px}
  .kpi .foot{font-size:12px; color:var(--faint); margin-top:6px}
  .num.pos{color:var(--pos)} .num.neu{color:var(--neu)} .num.neg{color:var(--neg)}
  .num.accent{color:var(--accent)} .num.base{color:var(--brand)}

  .panel h3{font-size:14px; font-weight:750; letter-spacing:-.01em; margin-bottom:14px; display:flex; align-items:center; gap:9px}
  .panel h3 .ic{width:8px;height:8px;border-radius:3px}
  .muted{color:var(--muted); font-weight:500}
  .small{font-size:12px; color:var(--faint)}

  /* distribution rows */
  .row1{grid-template-columns:1fr 1fr 1fr; margin-top:16px}
  .row2{grid-template-columns:1.15fr 1fr; margin-top:16px}
  .row3{grid-template-columns:1fr 1fr; margin-top:16px}
  .bars{display:flex; flex-direction:column; gap:13px}
  .b-item .b-top{display:flex; justify-content:space-between; align-items:baseline; font-size:12.5px; margin-bottom:5px}
  .b-top .bl{font-weight:650; color:#334155}
  .b-top .bv{font-weight:700; color:var(--ink)}
  .b-top .bp{color:var(--faint); font-weight:500; margin-left:6px}
  .track{height:22px; background:#edf0f6; border-radius:7px; overflow:hidden; position:relative}
  .fill{position:absolute; inset:0 auto 0 0; height:100%; border-radius:7px; min-width:3px;
        transition:width .5s cubic-bezier(.2,.8,.2,1)}
  .fill.zero{width:0 !important; min-width:0}
  .bar-label-inside{position:absolute; left:9px; top:0; height:100%; display:flex; align-items:center;
        color:#fff; font-size:11.5px; font-weight:800; z-index:1}
  .group{display:flex; flex-direction:column; gap:14px}
  .dual{display:grid; grid-template-columns:1fr 1fr; gap:8px}
  .dual .d-top{display:flex; justify-content:space-between; font-size:11.5px; color:var(--muted); font-weight:600; margin-bottom:4px}
  .dual .dl{font-weight:650; color:#334155}

  /* confusion matrix */
  .cm{display:grid; grid-template-columns:auto 1fr 1fr 1fr; gap:8px; align-items:stretch}
  .cm .chead{text-align:center; font-size:11px; font-weight:750; color:var(--muted); letter-spacing:.03em}
  .cm .rhead{text-align:right; font-size:11.5px; font-weight:750; color:var(--muted); padding-right:6px; white-space:nowrap}
  .cm .cell{border-radius:10px; padding:11px 10px; text-align:center; border:1px solid transparent}
  .cm .cell b{font-size:22px; font-weight:800; display:block; letter-spacing:-.02em}
  .cm .cell span{font-size:11px; color:var(--muted); font-weight:600}
  .cm .corr-pos{background:var(--pos-soft); border-color:#bfe6d5}
  .cm .corr-neu{background:var(--neu-soft); border-color:#f5ddb0}
  .cm .corr-neg{background:var(--neg-soft); border-color:#f5c2c9}
  .cm .off{background:#f7f8fb; border-color:var(--line)}
  .cm .corner{color:var(--faint); font-size:11px; font-weight:700}
  .cm .rowpct{grid-column:span 1; align-self:center; font-size:10.5px; color:var(--faint); padding-left:2px}

  /* accuracy bars */
  .acc-rows{display:flex; flex-direction:column; gap:15px}
  .acc-item .a-top{display:flex; justify-content:space-between; font-size:13px; font-weight:650; margin-bottom:6px}
  .a-top small{color:var(--muted); font-weight:500}
  .a-top b{font-weight:800}
  .atrack{height:12px; background:#edf0f6; border-radius:99px; overflow:hidden}
  .afill{height:100%; border-radius:99px}

  /* emotions distribution */
  .emo-grid{display:grid; grid-template-columns:1fr 1fr; gap:24px}
  .legend{display:flex; gap:16px; flex-wrap:wrap; font-size:12px; color:var(--muted); margin-top:14px}
  .legend i{width:10px;height:10px;border-radius:3px;display:inline-block;margin-right:6px;vertical-align:-1px}
  .agree-note{background:var(--accent-soft); color:var(--accent); border-radius:10px; padding:12px 14px; font-size:13px; font-weight:650}

  /* table */
  .table-card{padding:0; overflow:hidden; margin-top:16px}
  .toolbar{display:flex; flex-wrap:wrap; gap:12px; align-items:center; justify-content:space-between; padding:16px 20px; border-bottom:1px solid var(--line)}
  .filters{display:flex; flex-wrap:wrap; gap:10px; align-items:center}
  .seg{display:inline-flex; background:#edf0f6; border-radius:10px; padding:3px; gap:2px}
  .seg button{border:0; background:transparent; padding:7px 14px; border-radius:8px; font-size:12.5px; font-weight:650; color:var(--muted); cursor:pointer; transition:all .15s}
  .seg button.active{background:#fff; color:var(--ink); box-shadow:var(--shadow)}
  select{font-family:inherit; font-size:12.5px; padding:8px 9px; border:1px solid var(--line); border-radius:9px; background:#fff; color:var(--ink); font-weight:600; cursor:pointer}
  .search{flex:1; min-width:190px}
  .search input{width:100%; font-family:inherit; font-size:12.5px; padding:9px 11px; border:1px solid var(--line); border-radius:9px; background:#fff; outline:none}
  .search input:focus{border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-soft)}
  .count-line{padding:11px 20px; font-size:12.5px; color:var(--muted); border-bottom:1px solid var(--line); background:#fafbfe; display:flex; justify-content:space-between}
  .count-line b{color:var(--ink)}
  .scroll{overflow:auto; max-height:560px}
  table{width:100%; border-collapse:collapse; font-size:12.5px}
  thead th{position:sticky; top:0; background:#fafbfe; text-align:left; z-index:2; color:var(--faint); font-size:10.5px; text-transform:uppercase; letter-spacing:.06em; padding:10px 20px; border-bottom:1px solid var(--line); cursor:pointer; white-space:nowrap}
  thead th:hover{color:var(--accent)}
  tbody td{padding:11px 20px; border-bottom:1px solid #f0f2f7; vertical-align:top}
  tbody tr:hover{background:#fafbff}
  .t-rating{font-weight:750; width:84px}
  .t-star{color:var(--neu); letter-spacing:1px; font-size:11px}
  .t-big{max-width:400px}
  .t-title{font-weight:700; color:#1e293b}
  .t-txt{color:var(--muted); margin-top:2px; display:block}
  .pill{display:inline-block; padding:2px 9px; border-radius:999px; font-size:10.5px; font-weight:750; letter-spacing:.02em; white-space:nowrap}
  .pill.pos{background:var(--pos-soft); color:var(--pos)} .pill.neu{background:var(--neu-soft); color:var(--neu)} .pill.neg{background:var(--neg-soft); color:var(--neg)}
  .pill.none{background:#eef2f7; color:#64748b}
  .st{font-weight:750; font-size:12px}
  .st.ok{color:var(--pos)} .st.bad{color:var(--neg)}
  .floor{opacity:.75}
  .empty{padding:40px; text-align:center; color:var(--faint)}
  footer{margin-top:26px; color:var(--faint); font-size:12px; text-align:center; max-width:1240px; margin-left:auto; margin-right:auto; padding:0 28px}
  @media (max-width:1080px){ .kpis{grid-template-columns:repeat(3,1fr)} .row1,.row2,.row3,.emo-grid{grid-template-columns:1fr} .dual{grid-template-columns:1fr} }
  @media (max-width:600px){ .kpis{grid-template-columns:repeat(2,1fr)} .section{padding:0 16px} }
</style>
</head>
<body>

<div class="top">
  <div class="wrap">
    <div class="eyebrow">MBAX 6418 · Assignment 1 · Final Results</div>
    <h1>Three-Class Sentiment &amp; Emotion — Balanced Review Analysis</h1>
    <div class="sub">150 balanced Amazon Gift Card reviews (50 POSITIVE / 50 NEUTRAL / 50 NEGATIVE).
      LLM: DeepSeek-V4-Flash-0731 (temperature 0.0) — sees title + text only, never the rating.
      NRC Emotion Lexicon v0.92 for the word-list method. Data embedded — works offline.</div>
    <div class="chips">
      <span class="chip">Label rule: 4–5 POSITIVE · 3 NEUTRAL · 1–2 NEGATIVE</span>
      <span class="chip">Sample seed 6418</span>
      <span class="chip">Sentiment + primary emotion</span>
    </div>
  </div>
</div>

<div class="section">
  <!-- Headline metrics -->
  <div class="grid kpis" id="kpis"></div>

  <div class="grid row1">
    <div class="card panel">
      <h3><span class="ic" style="background:var(--neu)"></span>Star rating distribution</h3>
      <div class="bars" id="stars"></div>
    </div>
    <div class="card panel">
      <h3><span class="ic" style="background:var(--accent)"></span>Actual sentiment</h3>
      <div class="bars" id="actualDist"></div>
    </div>
    <div class="card panel">
      <h3><span class="ic" style="background:#7c8db5"></span>Predicted sentiment</h3>
      <div class="bars" id="predDist"></div>
    </div>
  </div>

  <div class="grid row3">
    <div class="card panel">
      <h3><span class="ic" style="background:var(--accent)"></span>Actual vs predicted</h3>
      <div class="bars" id="actPred"></div>
      <div class="legend">
        <span><i style="background:#9aa3b8"></i>Actual</span>
        <span><i style="background:var(--accent)"></i>Predicted</span>
      </div>
    </div>
    <div class="card panel">
      <h3><span class="ic" style="background:var(--neu)"></span>Accuracy by sentiment class</h3>
      <div class="acc-rows" id="accRows"></div>
    </div>
  </div>

  <div class="grid row2">
    <div class="card panel">
      <h3><span class="ic" style="background:var(--accent)"></span>3 × 3 confusion matrix <span class="muted small">(rows = actual, cols = predicted)</span></h3>
      <div class="cm" id="cm"></div>
    </div>
    <div class="card panel">
      <h3><span class="ic" style="background:var(--neu)"></span>Emotions — LLM vs NRC</h3>
      <div class="agree-note" id="agreeNote"></div>
      <div class="bars" id="emoCompare" style="margin-top:14px"></div>
      <div class="legend">
        <span><i style="background:var(--accent)"></i>LLM</span>
        <span><i style="background:var(--neu)"></i>NRC</span>
      </div>
    </div>
  </div>

  <div class="grid row1">
    <div class="card panel">
      <h3><span class="ic" style="background:#6366f1"></span>LLM emotion distribution</h3>
      <div class="bars" id="llmEmo"></div>
    </div>
    <div class="card panel">
      <h3><span class="ic" style="background:#f59e0b"></span>NRC emotion distribution</h3>
      <div class="bars" id="nrcEmo"></div>
    </div>
    <div class="card panel">
      <h3><span class="ic" style="background:#14b8a6"></span>Emotion agreement by class</h3>
      <div class="bars" id="emoByClass"></div>
    </div>
  </div>

  <!-- Review explorer -->
  <div class="card table-card">
    <div class="toolbar">
      <div class="filters">
        <div class="seg" id="statusSeg">
          <button data-v="all" class="active">All</button>
          <button data-v="correct">Correct</button>
          <button data-v="mismatch">Mismatched</button>
        </div>
        <select id="fActual" title="Filter actual sentiment"><option value="all">Any actual</option></select>
        <select id="fPred" title="Filter predicted sentiment"><option value="all">Any predicted</option></select>
        <select id="fLLM" title="Filter LLM emotion"><option value="all">Any LLM emotion</option></select>
        <select id="fNRC" title="Filter NRC emotion"><option value="all">Any NRC emotion</option></select>
      </div>
      <div class="search"><input id="search" placeholder="Search title or review text…"></div>
    </div>
    <div class="count-line">
      <span>Showing <b id="visibleCount">0</b> of <b id="totalCount">0</b> reviews</span>
      <span id="filterDesc"></span>
    </div>
    <div class="scroll">
      <table>
        <thead><tr>
          <th data-k="r">Rating</th><th data-k="t">Title / Review</th>
          <th data-k="a">Actual</th><th data-k="p">Predicted</th>
          <th data-k="c">Status</th><th>LLM emotion</th><th>NRC emotion</th>
        </tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>

  <footer>Built automatically from <code>data/step6_balanced_results.csv</code> · all numbers computed from the embedded data · filters update the live count · fully offline</footer>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById("data").textContent);
const CLS=["POSITIVE","NEUTRAL","NEGATIVE"];
const EMO=["anger","anticipation","disgust","fear","joy","sadness","surprise","trust"];
const CCOL={POSITIVE:"var(--pos)",NEUTRAL:"var(--neu)",NEGATIVE:"var(--neg)"};
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const pct=(n,d)=>d?(100*n/d).toFixed(1)+"%":"—";
const stars=n=>"★".repeat(Math.round(n))+"☆".repeat(5-Math.round(n));

/* ---------- stats (computed from the embedded data) ---------- */
const S=(()=>{
  const total=DATA.length, n_correct=DATA.filter(d=>d.c).length;
  const actual={POSITIVE:0,NEUTRAL:0,NEGATIVE:0}, pred={POSITIVE:0,NEUTRAL:0,NEGATIVE:0};
  const cm={}; CLS.forEach(a=>CLS.forEach(p=>cm[a+'-'+p]=0));
  const st={1:0,2:0,3:0,4:0,5:0};
  const le={},ne={}; EMO.forEach(e=>{le[e]=0;ne[e]=0;}); le['none']=0; ne['none']=0;
  const leMap={},neMap={};
  DATA.forEach(d=>{
    actual[d.a]++; pred[d.p]++;
    cm[d.a+'-'+d.p]++;
    const s=Math.round(d.r); if(s>=1&&s<=5) st[s]++;
    le[d.le||'none']++; ne[d.ne||'none']++;
    leMap[d.le||'none']=1; neMap[d.ne||'none']=1;
  });
  const per={}; CLS.forEach(c=>per[c]= actual[c]? cm[c+'-'+c]/actual[c] : null);
  let both=0,agree=0; DATA.forEach(d=>{ if(d.le&&d.ne){both++; if(d.le===d.ne)agree++;} });
  const emoByClass={};
  CLS.forEach(c=>{ emoByClass[c]={}; EMO.forEach(e=>emoByClass[c][e]=0); });
  EMO.forEach(e=>{});
  DATA.forEach(d=>{ if(d.le) emoByClass[d.a][d.le]=(emoByClass[d.a][d.le]||0)+1; });
  return {total,n_correct,acc:n_correct/total,actual,pred,cm,st,le,ne,per,
          both,agree,emoByClass,leKeys:Object.keys(leMap),neKeys:Object.keys(neMap)};
})();

/* ---------- headline KPIs ---------- */
const kpis=[
  {v:S.total, lab:"Balanced reviews", foot:"50 each class", cls:"base"},
  {v:pct(S.n_correct,S.total), lab:"Overall accuracy", foot:S.n_correct+" / "+S.total+" correct", cls:"accent"},
  {v:pct(S.cm["POSITIVE-POSITIVE"],S.actual.POSITIVE), lab:"POSITIVE accuracy", foot:S.actual.POSITIVE+" reviews", cls:"pos"},
  {v:pct(S.cm["NEUTRAL-NEUTRAL"],S.actual.NEUTRAL), lab:"NEUTRAL accuracy", foot:S.actual.NEUTRAL+" reviews", cls:"neu"},
  {v:pct(S.cm["NEGATIVE-NEGATIVE"],S.actual.NEGATIVE), lab:"NEGATIVE accuracy", foot:S.actual.NEGATIVE+" reviews", cls:"neg"},
  {v:agreeRate(), lab:"LLM vs NRC emotions", foot:S.agree+" agree of "+S.both, cls:"accent"},
];
document.getElementById("kpis").innerHTML=kpis.map(k=>
  `<div class="card kpi"><div class="lab">${k.lab}</div><div class="num ${k.cls}">${k.v}</div><div class="foot">${k.foot}</div></div>`).join("");
function agreeRate(){ return S.both? (100*S.agree/S.both).toFixed(1)+"%" : "—"; }

/* ---------- chart helpers (small-value safe) ---------- */
function barRow(label, value, max, color, countLabel){
  const w = value>0 ? Math.max(2.2, 100*value/max) : 0;
  const zero = value===0 ? " zero" : "";
  const lbl = value>0 && value>=max*0.09 ? `<span class="bar-label-inside">${value}</span>` : "";
  return `<div class="b-item">
    <div class="b-top"><span class="bl">${label}</span>
      <span><b class="bv">${countLabel==null?value:countLabel}</b>${max?`<span class="bp">${(100*value/max).toFixed(0)}% of peak</span>`:""}</span></div>
    <div class="track"><div class="fill${zero}" style="width:${w}%;background:${color}"></div>${lbl}</div>
  </div>`;
}
function barRows(items, max){
  // items: [{label, value, color}]
  return items.map(it=>barRow(it.label, it.value, max, it.color, it.value)).join("");
}

/* ---------- distributions ---------- */
document.getElementById("stars").innerHTML=barRows(
  [1,2,3,4,5].map(s=>({label:s+" star", value:S.st[s], color:"#f59e0b"})), Math.max.apply(null,[1,2,3,4,5].map(s=>S.st[s])));
document.getElementById("actualDist").innerHTML=barRows(
  CLS.map(c=>({label:c, value:S.actual[c], color:CCOL[c]})), Math.max(...CLS.map(c=>S.actual[c])));
document.getElementById("predDist").innerHTML=barRows(
  CLS.map(c=>({label:c, value:S.pred[c], color:CCOL[c]})), Math.max(...CLS.map(c=>S.pred[c])));

/* actual vs predicted grouped */
document.getElementById("actPred").innerHTML=CLS.map(c=>{
  const m=Math.max(S.actual[c],S.pred[c]);
  return barRow("Actual "+c, S.actual[c], m, "#9aa3b8") +
         `<div style="height:6px"></div>` +
         barRow("Pred   "+c, S.pred[c], S.actual[c]||S.pred[c]||1, CCOL[c]);
}).join("");

/* accuracy by class */
const accCols={POSITIVE:"var(--pos)",NEUTRAL:"var(--neu)",NEGATIVE:"var(--neg)",ALL:"var(--accent)"};
function accRow(label, rate, n, color){
  return `<div class="acc-item"><div class="a-top"><span>${label} <small>· ${n} reviews${label==="OVERALL"?"":" · "+ (100*rate).toFixed(1)+"%"}</small></span><b>${(100*rate).toFixed(1)}%</b></div>
    <div class="atrack"><div class="afill" style="width:${100*rate}%;background:${color}"></div></div></div>`;
}
document.getElementById("accRows").innerHTML=
  accRow("POSITIVE",S.per.POSITIVE,S.actual.POSITIVE,"var(--pos)")+
  accRow("NEUTRAL",S.per.NEUTRAL,S.actual.NEUTRAL,"var(--neu)")+
  accRow("NEGATIVE",S.per.NEGATIVE,S.actual.NEGATIVE,"var(--neg)")+
  accRow("OVERALL",S.acc,S.total,"var(--accent)");

/* confusion matrix */
let cmHTML=`<div class="corner"></div>
  <div class="chead" style="color:var(--pos)">POSITIVE</div>
  <div class="chead" style="color:var(--neu)">NEUTRAL</div>
  <div class="chead" style="color:var(--neg)">NEGATIVE</div>`;
CLS.forEach(a=>{
  cmHTML+=
   `<div class="rhead">${a}</div>`+
   CLS.map(p=>{
     const v=S.cm[a+'-'+p];
     const cls=(a===p)?('corr-'+a.toLowerCase()):'off';
     const rp=S.actual[a]? (100*v/S.actual[a]) : 0;
     return `<div class="cell ${cls}"><b>${v}</b><span>${rp.toFixed(0)}%</span></div>`;
   }).join("")+
   `<div class="rowpct">${S.actual[a]} total</div>`;
});
document.getElementById("cm").innerHTML=cmHTML;

/* emotion distributions */
const maxLe=Math.max(...EMO.map(e=>S.le[e]), S.le['none']||0);
const maxNe=Math.max(...EMO.map(e=>S.ne[e]), S.ne['none']||0);
document.getElementById("llmEmo").innerHTML=barRows(
  EMO.map(e=>({label:e, value:S.le[e], color:"#6366f1"})).concat([{label:"none", value:S.le['none']||0, color:"#cbd5e1"}]), maxLe);
document.getElementById("nrcEmo").innerHTML=barRows(
  EMO.map(e=>({label:e, value:S.ne[e], color:"#f59e0b"})).concat([{label:"none", value:S.ne['none']||0, color:"#cbd5e1"}]), maxNe);

/* LLM vs NRC emotion comparison (paired) */
document.getElementById("emoCompare").innerHTML=EMO.map(e=>{
  const m=Math.max(S.le[e],S.ne[e],1);
  return `<div class="dual">
    <div><div class="d-top"><span class="dl">${e}</span><span>LLM ${S.le[e]} · NRC ${S.ne[e]}</span></div>
      <div class="track"><div class="fill ${S.le[e]===0?'zero':''}" style="width:${S.le[e]?Math.max(3,100*S.le[e]/m):0}%;background:var(--accent)"></div></div></div>
  </div><div style="height:8px"></div>`;
}).join("");

/* emotion agreement note + by-class */
document.getElementById("agreeNote").innerHTML=
  `LLM vs NRC primary-emotion agreement: <b>${S.agree}/${S.both}</b> reviews (${agreeRate()} of those with both).`;
const maxEC=Math.max(...EMO.map(e=>{ let m=0; CLS.forEach(c=>m=Math.max(m,S.emoByClass[c][e]||0)); return m;}));
document.getElementById("emoByClass").innerHTML=CLS.map(c=>
  `<div class="b-item"><div class="b-top"><span class="bl">${c} reviews — LLM emotion</span></div>`
  +EMO.map(e=>{
    const v=S.emoByClass[c][e]||0, m=maxEC||1;
    return `<div style="margin:3px 0"><div class="track" style="height:12px">
      <div class="fill ${v===0?'zero':''}" style="width:${v?Math.max(3,100*v/maxEC):0}%;background:${CCOL[c]}"></div>
      <span style="position:absolute;left:${v?Math.max(3,100*v/maxEC):0}%;top:0;font-size:10px;color:#334155;margin-left:6px;line-height:12px;font-weight:700">${e} ${v}</span>
    </div></div>`;
  }).join("")+"</div>").join("");

/* ---------- review table ---------- */
let state={status:"all",actual:"all",pred:"all",le:"all",ne:"all",q:"",sort:"r",dir:-1};
const segBtns=document.querySelectorAll("#statusSeg button");
function initSelects(){
  const opt=(sel,vals,lab)=>vals.forEach(v=>{ const o=document.createElement("option"); o.value=v; o.textContent=lab(v); sel.appendChild(o); });
  ["fActual","fPred"].forEach(id=>opt(document.getElementById(id),CLS,v=>v));
  document.getElementById("fLLM").appendChild(new Option("Any LLM emotion","all"));
  [...new Set(DATA.map(d=>d.le||"none"))].sort().forEach(v=>document.getElementById("fLLM").appendChild(new Option(v||"none",v||"none")));
  document.getElementById("fNRC").appendChild(new Option("Any NRC emotion","all"));
  [...new Set(DATA.map(d=>d.ne||"none"))].sort().forEach(v=>document.getElementById("fNRC").appendChild(new Option(v||"none",v||"none")));
}
initSelects();
function visible(){
  const q=state.q.toLowerCase();
  return DATA.filter(d=>{
    if(state.status==="correct"&&!d.c)return false;
    if(state.status==="mismatch"&&d.c)return false;
    if(state.actual!=="all"&&d.a!==state.actual)return false;
    if(state.pred!=="all"&&d.p!==state.pred)return false;
    if(state.le!=="all"&&(d.le||"none")!==state.le)return false;
    if(state.ne!=="all"&&(d.ne||"none")!==state.ne)return false;
    if(q&&!(d.t.toLowerCase().includes(q)||d.x.toLowerCase().includes(q)))return false;
    return true;
  });
}
function render(){
  let list=visible();
  const k=state.sort, dir=state.dir;
  list.sort((a,b)=>{const av=k==="r"?a.r:(a[k]||"")||"", bv=k==="r"?b.r:(b[k]||"")||"";
    const c=(typeof av==="number")?av-bv:String(av).localeCompare(String(bv)); return c*dir;});
  document.getElementById("tbody").innerHTML=list.length?list.map(d=>`
    <tr>
      <td class="t-rating">${d.r.toFixed(1)}<div class="t-star">${stars(d.r)}</div></td>
      <td class="t-big"><div class="t-title">${esc(d.t)}</div><span class="t-txt">${esc(d.x)}</span></td>
      <td><span class="pill ${d.a.toLowerCase()}">${d.a}</span></td>
      <td><span class="pill ${d.p.toLowerCase()}">${d.p}</span></td>
      <td><span class="st ${d.c?'ok':'bad'}">${d.c?'✓ Correct':'✗ Mismatch'}</span></td>
      <td><span class="pill ${d.le?'':'none'}" style="text-transform:capitalize">${esc(d.le||'none')}</span></td>
      <td><span class="pill ${d.ne?'':'none'}" style="text-transform:capitalize">${esc(d.ne||'none')}</span></td>
    </tr>`).join(""):`<tr><td colspan="7"><div class="empty">No reviews match the current filters.</div></td></tr>`;
  document.getElementById("visibleCount").textContent=list.length;
  document.getElementById("totalCount").textContent=S.total;
  const parts=[]; if(state.status!=="all")parts.push(state.status);
  ["actual","pred"].forEach(k=>{if(state[k]!=="all")parts.push(k+"="+state[k]);});
  ["le","ne"].forEach(k=>{if(state[k]!=="all")parts.push(k+"="+state[k]);});
  document.getElementById("filterDesc").textContent=parts.length?("filtered: "+parts.join(", ")):"";
}
document.getElementById("statusSeg").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
  segBtns.forEach(x=>x.classList.remove("active"));b.classList.add("active");state.status=b.dataset.v;render();});
const FILT_MAP={fActual:"actual",fPred:"pred",fLLM:"le",fNRC:"ne"};
["fActual","fPred","fLLM","fNRC"].forEach(id=>document.getElementById(id).addEventListener("change",e=>{
  state[FILT_MAP[id]]=e.target.value; render(); }));
document.getElementById("search").addEventListener("input",e=>{state.q=e.target.value;render();});
document.querySelectorAll("thead th[data-k]").forEach(th=>th.addEventListener("click",()=>{
  const k=th.dataset.k; if(state.sort===k)state.dir*=-1; else{state.sort=k;state.dir=k==="r"?-1:1;} render(); }));
render();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Build + verify
# ---------------------------------------------------------------------------
def main():
    rows = load_rows()
    stats = compute_stats(rows)
    html = HTML.replace("__DATA__", emit_data(rows))
    OUT_PATH.write_text(html, encoding="utf-8")
    print("Dashboard written:", OUT_PATH)
    print(f"size: {OUT_PATH.stat().st_size/1024:.1f} KB | rows embedded: {len(rows)}")
    print("\n--- BUILD-TIME VERIFICATION (Python, independent of JS) ---")
    print(f"total={stats['total']} correct={stats['n_correct']} overall={stats['overall']*100:.2f}%")
    print("per-class acc:", {c: (f"{v*100:.1f}%" if v is not None else None)
                             for c, v in stats['per'].items()})
    print("actual:", stats['actual'], "predicted:", stats['pred'])
    print("confusion:")
    for a in CLASSES:
        print("  ", a, {p: stats['cm'][f"{a}-{p}"] for p in CLASSES})
    print("stars:", stats['stars'])
    print("LLM emotions:", {k: v for k, v in stats['llm_dist'].items() if v})
    print("NRC emotions :", {k: v for k, v in stats['nrc_dist'].items() if v})
    print("LLM-vs-NRC agreement:", stats['emo_agree'], "/", stats['emo_both'])


if __name__ == "__main__":
    main()
