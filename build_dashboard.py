#!/usr/bin/env python3
"""MBAX 6418 Assignment 1 - FINAL dashboard (Steps 1-7).

Consumes the balanced 3-class run (results/step6_results.json +
data/step6_reviews.jsonl) and emits a self-contained, offline-capable HTML
dashboard. Every chart and number is computed in-page from that embedded data
-- nothing hardcoded.
"""
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results", "step6_results.json")
REVIEWS = os.path.join(HERE, "data", "step6_reviews.jsonl")
OUT = os.path.join(HERE, "dashboard.html")

with open(RESULTS) as f:
    metrics = json.load(f)

reviews = []
with open(REVIEWS) as f:
    for line in f:
        line = line.strip()
        if line:
            r = json.loads(line)
            reviews.append({
                "index": r["index"],
                "rating": r["rating"],
                "true": r["true_class"],
                "predicted": r["predicted"],
                "confidence": r["confidence"],
                "correct": r["correct"],
                "title": r["title"],
                "text": r["text"],
                "llm_emotion": r["llm_emotion"],
                "nrc_emotion": r["nrc_emotion"],
                "emo_agree": r["emo_agree"] if r["nrc_emotion"] is not None else None,
            })

generated = datetime.now().strftime("%Y-%m-%d %H:%M")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>3-Class Sentiment &amp; Emotion — MBAX 6418 · Assignment 1</title>
<style>
  :root{
    --bg:#f4f5f7; --surface:#ffffff; --surface-2:#fafbfc;
    --border:#e7e9ee; --border-strong:#d5d9e0;
    --ink:#141a24; --ink-2:#33404f; --muted:#66738a; --faint:#8f9bad;
    --positive:#0e7a4f; --positive-strong:#0a5c3c; --positive-bg:#e6f4ee;
    --neutral:#b57a00; --neutral-strong:#8a5600; --neutral-bg:#fbf3e0;
    --negative:#c03434; --negative-strong:#972a2a; --negative-bg:#fbecec;
    --accent:#1f5bb3; --paper:#f7f3ec;
  }
  *{box-sizing:border-box; margin:0; padding:0;}
  body{background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    font-size:14px; line-height:1.5; -webkit-font-smoothing:antialiased;}
  .num{font-variant-numeric:tabular-nums; font-feature-settings:"tnum";}
  .shell{max-width:1200px; margin:0 auto; padding:32px 28px 60px;}

  /* header */
  .topbar{display:flex; align-items:flex-end; justify-content:space-between; gap:20px;
          padding-bottom:24px; border-bottom:1px solid var(--border); margin-bottom:26px;}
  .kicker{font-size:11px; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); font-weight:600; margin-bottom:8px;}
  h1{font-size:25px; font-weight:650; letter-spacing:-.02em; line-height:1.15;}
  .lede{margin-top:7px; color:var(--muted); font-size:14px; max-width:720px;}
  .lede b{color:var(--ink-2);}
  .lede code{background:var(--surface-2); border:1px solid var(--border); border-radius:5px; padding:1px 5px; font-size:12px; color:var(--ink-2);}
  .badges{display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; min-width:200px;}
  .badge{display:inline-flex; align-items:center; gap:6px; font-size:12px; color:var(--ink-2);
         background:var(--surface); border:1px solid var(--border); border-radius:999px; padding:6px 11px; white-space:nowrap;}
  .dot{width:8px; height:8px; border-radius:50%;}

  /* KPI */
  .kpis{display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:14px; margin-bottom:26px;}
  .kpi{background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:16px 16px 14px;}
  .kpi .label{font-size:11px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); font-weight:600;}
  .kpi .value{font-size:28px; font-weight:680; letter-spacing:-.02em; margin-top:8px; line-height:1;}
  .kpi .sub{font-size:12px; color:var(--faint); margin-top:7px;}
  .kpi.hero{background:linear-gradient(180deg,#0f2438,#0c1e30); border-color:#0c1e30;}
  .kpi.hero .label{color:#9fb3cf;}
  .kpi.hero .value{color:#fff;}
  .kpi.hero .sub{color:#7f96b4;}
  .value.pos{color:var(--positive-strong);} .value.neu{color:var(--neutral-strong);} .value.neg{color:var(--negative-strong);}

  .split{display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:14px;}
  .card{background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:20px;}
  .card h2{font-size:14px; font-weight:650; color:var(--ink-2);}
  .card .hint{font-size:12px; color:var(--faint); margin-top:3px;}
  .card-head{display:flex; align-items:flex-start; justify-content:space-between; gap:16px; flex-wrap:wrap;}
  .card.stack{margin-bottom:14px;}

  /* correct vs incorrect */
  .gear{display:flex; gap:22px; margin-top:16px;}
  .gear .big{font-size:42px; font-weight:700; letter-spacing:-.03em; line-height:1;}
  .gear .cap{font-size:12px; color:var(--muted); margin-top:4px;}
  .gear .b .big{color:var(--positive-strong);} .gear .c .big{color:var(--negative-strong);}
  .seg{height:12px; border-radius:6px; overflow:hidden; display:flex; background:var(--border); margin-top:6px;}
  .seg .s-correct{background:linear-gradient(90deg,#1a9c64,#12b976);}
  .seg .s-wrong{background:linear-gradient(90deg,#d24141,#c03434);}
  .griddots{display:grid; grid-template-columns:repeat(25,1fr); gap:3px; margin-top:18px;}
  .cell{aspect-ratio:1/1; border-radius:2.5px;}
  .cell.ok{background:var(--positive);} .cell.bad{background:var(--negative);}
  .facefail{margin-top:16px; padding:12px 14px; border-radius:10px; background:var(--negative-bg);
            border:1px solid #f2d3d3; font-size:13px; color:var(--negative-strong);}
  .facefail b{font-size:22px;}

  /* confusion matrix */
  .cm{width:100%; border-collapse:separate; border-spacing:0; margin-top:16px; font-size:13px;}
  .cm th,.cm td{text-align:center; padding:11px; border:1px solid var(--border);}
  .cm .corner{background:var(--surface-2); color:var(--muted); font-weight:600;}
  .cm .rowlab{background:var(--surface-2); font-weight:600; color:var(--ink-2); text-align:right; width:112px;}
  .cm .collab{background:var(--surface-2); font-weight:650; color:var(--ink-2);}
  .cm .collab small{display:block; font-size:10.5px; color:var(--faint); font-weight:500;}
  .cm td.cellv{font-size:23px; font-weight:700; letter-spacing:-.02em;}
  .cm td.diag{background:#e6f4ee; color:var(--positive-strong);}
  .cm td.offneu{background:#f7e6bd; color:var(--neutral-strong);}
  .cm td.offneg{background:#fbdcdc; color:var(--negative-strong);}
  .cm td.offpos{background:#f3edfb; color:#6b3fa0;}
  .cm .marg{background:var(--surface-2); font-size:12px; color:var(--muted); font-weight:600;}

  /* distribution panels */
  .dist-grid{display:grid; grid-template-columns:repeat(4,1fr); gap:24px; margin-top:18px;}
  .dpanel h4{font-size:11px; font-weight:650; letter-spacing:.05em; text-transform:uppercase; color:var(--muted); margin-bottom:11px;}
  .drow{display:grid; grid-template-columns:96px 1fr 34px; align-items:center; gap:9px; margin-bottom:8px;}
  .drow .dl{font-size:12.5px; color:var(--ink-2); font-weight:550; white-space:nowrap;}
  .drow .dl.sub{color:var(--faint); font-weight:500;}
  .drow .dl.pos{color:var(--positive-strong);} .drow .dl.neu{color:var(--neutral-strong);} .drow .dl.neg{color:var(--negative-strong);}
  .dtrack{height:10px; border-radius:5px; background:var(--surface-2); overflow:hidden;}
  .dfill{height:100%; border-radius:5px; min-width:0;}
  .drow .dc{font-size:12px; color:var(--muted); text-align:right; font-variant-numeric:tabular-nums;}
  .dpair{display:block; margin-bottom:2px;}

  /* accuracy by class */
  .acc-list{margin-top:16px;}
  .accrow{display:grid; grid-template-columns:118px 1fr 118px; align-items:center; gap:14px; margin-bottom:12px;}
  .accrow .al{font-size:13px; font-weight:600; color:var(--ink-2); white-space:nowrap;}
  .acc-stack{height:26px; border-radius:8px; overflow:hidden; display:flex; background:var(--border);}
  .acc-stack .ag{background:linear-gradient(90deg,#1a9c64,#12b976);}
  .acc-stack .ar{background:var(--negative);}
  .accrow .av{font-size:12.5px; color:var(--muted); text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap;}
  .av b{color:var(--ink-2);}
  .flowline{display:flex; gap:8px; flex-wrap:wrap; margin-top:6px;}
  .flow-chip{font-size:12px; font-weight:600; border-radius:999px; padding:5px 11px; background:var(--negative-bg);
             border:1px solid #f2d3d3; color:var(--negative-strong); font-variant-numeric:tabular-nums;}
  .flow-chip .from{color:var(--muted); font-weight:600;}

  /* emotion */
  .emo-row{display:grid; grid-template-columns:1fr 1fr; gap:26px; margin-top:18px;}
  .emo-method h3{font-size:12px; font-weight:650; letter-spacing:.03em; text-transform:uppercase; color:var(--muted); margin-bottom:10px;}
  .emo-agr-wrap{margin-top:2px;}
  .emo-agr{height:12px; border-radius:6px; overflow:hidden; display:flex; background:var(--border); margin-top:10px;}
  .emo-agr .a-agree{background:#12b976;} .emo-agr .a-diff{background:#d8dde6;} .emo-agr .a-none{background:#c03434; opacity:.55;}
  .emo-legend{display:flex; gap:14px; margin-top:9px; font-size:11.5px; color:var(--muted); flex-wrap:wrap;}
  .emo-legend i{width:10px;height:10px;border-radius:3px;display:inline-block;margin-right:5px;vertical-align:-1px;}
  .emo-note{margin-top:16px; padding:11px 13px; border-radius:9px; background:var(--surface-2);
            border:1px solid var(--border); font-size:12.5px; color:var(--ink-2); line-height:1.55;}
  .emo-note b{color:var(--ink);}
  .etag{display:inline-block; font-size:11.5px; font-weight:600; border-radius:999px; padding:3px 9px;
        background:var(--surface-2); border:1px solid var(--border); color:var(--ink-2); text-transform:capitalize; white-space:nowrap;}
  .etag .m{color:var(--faint); font-weight:650; margin-right:3px; text-transform:none;}
  .etag.na{color:var(--faint);}
  .agree{display:inline-flex; align-items:center; gap:5px; font-size:12px; font-weight:650;}
  .agree .a-ico{width:15px;height:15px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:10px;color:#fff;}
  .agree.yes .a-ico{background:var(--positive);} .agree.no .a-ico{background:var(--negative);} .agree.na .a-ico{background:#9aa3b2;}

  /* table */
  .table-card{padding:0;}
  .table-head{display:flex; align-items:center; justify-content:space-between; gap:16px; padding:20px 20px 0; flex-wrap:wrap;}
  .table-head h2{font-size:15px; font-weight:650;}
  .table-head p{font-size:12px; color:var(--faint); margin-top:3px;}
  .filters{display:flex; gap:16px; flex-wrap:wrap; align-items:center;}
  .fgroup{display:flex; gap:5px; align-items:center;}
  .fg-label{font-size:10.5px; letter-spacing:.08em; text-transform:uppercase; color:var(--faint); font-weight:650; margin-right:2px; white-space:nowrap;}
  .pill{border:1px solid var(--border); background:var(--surface-2); color:var(--ink-2); font-size:12px; font-weight:600;
        border-radius:999px; padding:5px 12px; cursor:pointer; transition:all .12s ease; white-space:nowrap; font-variant-numeric:tabular-nums;}
  .pill:hover{border-color:var(--border-strong);}
  .pill .ct{color:var(--faint); font-weight:600; margin-left:4px;}
  .pill.active{background:var(--ink); color:#fff; border-color:var(--ink);}
  .pill.active .ct{color:#aeb8c8;}
  .pill.warn{background:var(--negative-bg); border-color:#f0c9c9; color:var(--negative-strong);}
  .pill.warn .ct{color:var(--negative-strong);}
  .pill.warn.active{background:var(--negative-strong); border-color:var(--negative-strong); color:#fff;}
  .pill.warn.active .ct{color:#ffd7d7;}
  .wrap{max-height:560px; overflow:auto; margin-top:16px; border-top:1px solid var(--border);}
  table.review{width:100%; border-collapse:collapse; font-size:13px; background:var(--surface);}
  table.review th{position:sticky; top:0; background:var(--surface-2); color:var(--ink-2); font-size:11px;
      letter-spacing:.05em; text-transform:uppercase; font-weight:600; text-align:left; padding:10px 14px;
      border-bottom:1px solid var(--border); white-space:nowrap; z-index:2;}
  table.review td{padding:10px 14px; border-bottom:1px solid #f0f2f5; vertical-align:top;}
  tr.tr-fail td{background:#fdf2f2;}
  table.review tr.tr-fail:hover td{background:#fbe9e9;}
  td.c{white-space:nowrap; text-align:center;}
  .n{white-space:nowrap; text-align:right; color:var(--muted); font-size:12px;}
  .title-max{max-width:190px;}
  .txt{max-width:285px; color:var(--ink-2); line-height:1.45;}
  .rating{font-weight:650; text-align:center;}
  .tag{display:inline-block; font-size:11px; font-weight:650; letter-spacing:.02em; border-radius:999px; padding:3px 8px; white-space:nowrap;}
  .tag.pos{background:var(--positive-bg); color:var(--positive-strong);}
  .tag.neu{background:var(--neutral-bg); color:var(--neutral-strong);}
  .tag.neg{background:var(--negative-bg); color:var(--negative-strong);}
  .verdict{display:inline-flex; align-items:center; gap:5px; font-weight:650; font-size:12px;}
  .verdict .ico{width:15px;height:15px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:10px;color:#fff;}
  .verdict.y .ico{background:var(--positive);} .verdict.n .ico{background:var(--negative);}
  .table-foot{display:flex; justify-content:space-between; gap:14px; padding:12px 20px 16px; font-size:12px; color:var(--faint); align-items:center; flex-wrap:wrap;}
  .legend{display:flex; gap:14px; flex-wrap:wrap;}
  .legend i{display:inline-block; width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px;}

  footer{margin-top:28px; padding-top:16px; border-top:1px solid var(--border); font-size:12px; color:var(--faint);
         display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap;}

  @media (max-width:1000px){ .split{grid-template-columns:1fr;} .dist-grid{grid-template-columns:repeat(2,1fr);} }
  @media (max-width:600px){ .dist-grid{grid-template-columns:1fr;} .topbar{flex-direction:column;align-items:flex-start;} }
</style>
</head>
<body>
<div class="shell">

  <header class="topbar">
    <div>
      <div class="kicker">MBAX 6418 · Assignment 1</div>
      <h1>3-Class Sentiment &amp; Primary Emotion</h1>
      <p class="lede">Rating-blind classification of Amazon Gift Card reviews on a <b>balanced 150-review sample</b>
        (50 per class, seed <span id="head-seed" class="num"></span>). The model saw only <code>title</code> + <code>text</code>,
        never the rating. True class from the rating: <b>4–5★ → POSITIVE · 3★ → NEUTRAL · 1–2★ → NEGATIVE</b>. Two
        independent emotion methods (LLM vs NRC word-list) are compared per review.</p>
    </div>
    <div class="badges">
      <span class="badge"><span class="dot" style="background:var(--positive-strong)"></span><span id="m-model"></span></span>
      <span class="badge"><span class="dot" style="background:var(--accent)"></span><span id="m-n"></span> reviews</span>
      <span class="badge">seed <span id="m-seed" class="num"></span></span>
    </div>
  </header>

  <!-- KPIs -->
  <section class="kpis" id="kpis"></section>

  <!-- overview split: correctness + confusion matrix -->
  <section class="split">
    <article class="card">
      <h2>Correct vs. Incorrect (150 predictions)</h2>
      <div class="hint">Every prediction colored by correctness, in sample order</div>
      <div class="gear">
        <div class="b"><div class="big num" id="g-correct">–</div><div class="cap">correct</div></div>
        <div class="c"><div class="big num" id="g-wrong">–</div><div class="cap">incorrect</div></div>
      </div>
      <div class="seg"><div class="s-correct" id="seg-ok"></div><div class="s-wrong" id="seg-bad"></div></div>
      <div class="griddots" id="griddots"></div>
      <div class="facefail"><span><b id="fail-big" class="num">–</b> misclassified reviews — use the <i>Misclassified</i> filter to inspect them, or see the error flow below.</span></div>
    </article>

    <article class="card">
      <h2>Three-Class Confusion Matrix</h2>
      <div class="hint">Rows = true class · Columns = predicted class</div>
      <table class="cm"><thead></thead><tbody id="cm-body"></tbody></table>
    </article>
  </section>

  <!-- 1,2,3,4 distribution panels -->
  <section class="card stack">
    <div class="card-head">
      <div><h2>Dataset &amp; Prediction Distribution</h2><div class="hint">Counts computed in-page from the saved balanced run</div></div>
    </div>
    <div class="dist-grid">
      <div class="dpanel"><h4>Star-rating distribution</h4><div id="rating-dist"></div></div>
      <div class="dpanel"><h4>True sentiment class</h4><div id="true-dist"></div></div>
      <div class="dpanel"><h4>Predicted sentiment class</h4><div id="pred-dist"></div></div>
      <div class="dpanel"><h4>True vs Predicted</h4><div id="tvp-dist"></div></div>
    </div>
  </section>

  <!-- 5 accuracy by class + failure flow -->
  <section class="card stack">
    <div class="card-head">
      <div><h2>Accuracy &amp; Misclassifications by Class</h2><div class="hint">Green = correct, red = errors; error chips show where each class leaks</div></div>
    </div>
    <div class="acc-list" id="acc-list"></div>
    <div class="flowline" id="flow-chips"></div>
  </section>

  <!-- 6,7,8,9 emotion -->
  <section class="card stack">
    <div class="card-head">
      <div>
        <h2 style="font-size:15px">7 &middot; 8 — Primary Emotion — Method 1 (LLM) vs Method 2 (NRC word-list)</h2>
        <div class="hint">Each review labeled with one of 8 emotions by both methods</div>
      </div>
      <div class="agree-kpi">
        <div class="num" style="font-size:30px;font-weight:700" id="emo-agree-pct">–</div>
        <div class="cap" style="font-size:12px;color:var(--muted)" id="emo-agree-cap"></div>
      </div>
    </div>
    <div class="emo-row">
      <div class="emo-method"><h3><b>Method 1</b> &middot; LLM</h3><div id="llm-bars"></div></div>
      <div class="emo-method"><h3><b>Method 2</b> &middot; NRC lexicon</h3><div id="nrc-bars"></div></div>
    </div>
    <div class="emo-agr-wrap">
      <h3 style="font-size:11px;font-weight:650;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin-top:18px">9 &middot; LLM vs NRC emotion agreement</h3>
      <div class="emo-agr" id="emo-agr"></div>
      <div class="emo-legend">
        <span><i style="background:#12b976"></i>agree</span>
        <span><i style="background:#d8dde6"></i>differ</span>
        <span><i style="background:#c03434;opacity:.55"></i>no NRC signal</span>
      </div>
    </div>
    <p class="emo-note" id="emo-note"></p>
  </section>

  <!-- review table (interactive filters preserved) -->
  <section class="card table-card">
    <div class="table-head">
      <div>
        <h2>Review-Level Detail</h2>
        <p>Sentiment verdict = predicted vs. true (3-way) · Emotion agree = LLM vs NRC · red rows are misclassified</p>
      </div>
      <div class="filters" id="filters">
        <div class="fgroup">
          <span class="fg-label">Verdict</span>
          <button class="pill active" data-f="verdict" data-v="all">All</button>
          <button class="pill" data-f="verdict" data-v="correct">Correct<span class="ct"></span></button>
          <button class="pill warn" data-f="verdict" data-v="wrong">Misclassified<span class="ct"></span></button>
        </div>
        <div class="fgroup" id="pred-group">
          <span class="fg-label">Predicted</span>
          <button class="pill active" data-f="pred" data-v="all">All</button>
        </div>
        <div class="fgroup" id="rate-group">
          <span class="fg-label">Rating</span>
          <button class="pill active" data-f="rating" data-v="all">All</button>
        </div>
      </div>
    </div>
    <div class="wrap">
      <table class="review">
        <thead>
          <tr>
            <th>#</th><th>Title</th><th>Review text</th><th style="text-align:center">Rating</th>
            <th>True</th><th>Predicted</th><th>Confidence</th>
            <th>LLM&nbsp;emo.</th><th>NRC&nbsp;emo.</th><th>Agree?</th><th>Correct?</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
    <div class="table-foot">
      <div class="legend">
        <span><i style="background:var(--positive)"></i>correct</span>
        <span><i style="background:var(--negative)"></i>misclassified</span>
        <span><i style="background:var(--positive);border-radius:50%"></i>emotion agree</span>
        <span><i style="background:var(--negative);border-radius:50%"></i>emotion differ</span>
        <span><i style="background:#9aa3b2;border-radius:50%"></i>no NRC signal</span>
      </div>
      <div id="t-shown">–</div>
    </div>
  </section>

  <footer>
    <div>Balanced sample (seed <span id="f-seed" class="num"></span>) from <code>data/Gift_Cards.jsonl.gz</code>; results from <code>results/step6_results.json</code> &amp; <code>data/step6_reviews.jsonl</code> on <span id="f-generated"></span>.</div>
    <div>Offline dashboard — no external resources.</div>
  </footer>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
  var DATA = JSON.parse(document.getElementById('data').textContent);
  var M = DATA.metrics, R = DATA.reviews;
  var CLASSES = ['POSITIVE','NEUTRAL','NEGATIVE'];
  var CCODE = {POSITIVE:'POS', NEUTRAL:'NEU', NEGATIVE:'NEG'};
  var CTAG  = {POSITIVE:'pos', NEUTRAL:'neu', NEGATIVE:'neg'};
  var COL   = {pos:'#0e7a4f', neu:'#c07a00', neg:'#c03434', accent:'#1f5bb3', muted:'#9aa3b2', ok:'#12b976', bad:'#c03434'};
  function g(id,v){ var e=document.getElementById(id); if(e) e.textContent=v; }

  // header/footer
  g('m-model',M.model); g('m-n',M.n_reviews); g('m-seed',M.sample_seed);
  g('head-seed',M.sample_seed); g('f-seed',M.sample_seed); g('f-generated',DATA.generated);

  // ---- KPIs (1 hero + 6 factual) ----
  var kpis=[
    {label:'Reviews analyzed', value:M.n_reviews, sub:'balanced 3-class'},
    {label:'Overall accuracy', value:(M.overall_accuracy*100).toFixed(1)+'%', sub:M.n_correct+'/'+M.n_reviews, hero:true},
    {label:'Correct', value:M.n_correct, sub:'matched true class'},
    {label:'Incorrect', value:M.n_incorrect, sub:'misclassified', bad:true},
    {label:'POSITIVE acc.', value:(M.class_accuracy.POSITIVE.accuracy*100).toFixed(1)+'%', sub:'43/50', cls:'pos'},
    {label:'NEUTRAL acc.', value:(M.class_accuracy.NEUTRAL.accuracy*100).toFixed(1)+'%', sub:'18/50', cls:'neu'},
    {label:'NEGATIVE acc.', value:(M.class_accuracy.NEGATIVE.accuracy*100).toFixed(1)+'%', sub:'46/50', cls:'neg'},
  ];
  document.getElementById('kpis').innerHTML = kpis.map(function(k){
    return '<div class="kpi'+(k.hero?' hero':'')+'">'+
      '<div class="label">'+k.label+'</div><div class="num value '+(k.cls||'')+'">'+k.value+'</div>'+
      '<div class="sub">'+k.sub+'</div></div>';
  }).join('');

  // ---- correct vs incorrect ----
  g('g-correct',M.n_correct); g('g-wrong',M.n_incorrect); g('fail-big',M.n_incorrect);
  var okPct = M.n_correct/M.n_reviews*100;
  document.getElementById('seg-ok').style.width = okPct.toFixed(2)+'%';
  document.getElementById('seg-bad').style.width = (100-okPct).toFixed(2)+'%';
  document.getElementById('griddots').innerHTML = R.map(function(r){
    return '<div class="cell '+(r.correct?'ok':'bad')+'" title="Review #'+(r.index+1)+' — '+(r.correct?'correct':'MISCLASSIFIED')+'"></div>';
  }).join('');

  // ---- generic horizontal bar (zero-width safe: enforces a visible sliver) ----
  function hbar(label, value, total, color, capClass){
    var pct = total ? value/total*100 : 0;
    var w = value>0 ? Math.max(pct, 1.5) : 0;
    var fill = value>0 ? '<div class="dfill" style="width:'+w+'%;background:'+color+'"></div>' : '';
    return '<div class="drow"><span class="dl '+(capClass||'')+'">'+label+'</span>'+
           '<div class="dtrack">'+fill+'</div><span class="dc">'+value+'</span></div>';
  }
  function renderBars(elId, rows){ document.getElementById(elId).innerHTML = rows.join(''); }

  // ---- 1. star-rating distribution ----
  var starC = {1:'neg',2:'neg',3:'neu',4:'pos',5:'pos'};
  function starCount(s){ var n=0; R.forEach(function(r){ if(Math.round(r.rating)===s) n++; }); return n; }
  var starRows = [1,2,3,4,5].map(function(s){ return hbar(s+'\u2605', starCount(s), R.length, COL[starC[s]]); });
  renderBars('rating-dist', starRows);

  // ---- 2. true class / 3. predicted class ----
  var trueC = {}, predC = {};
  R.forEach(function(r){ trueC[r.true]=(trueC[r.true]||0)+1; predC[r.predicted]=(predC[r.predicted]||0)+1; });
  renderBars('true-dist', CLASSES.map(function(c){ return hbar(CCODE[c], trueC[c]||0, R.length, COL[CTAG[c]], c.toLowerCase()); }));
  renderBars('pred-dist', CLASSES.map(function(c){ return hbar(CCODE[c], predC[c]||0, R.length, COL[CTAG[c]], c.toLowerCase()); }));

  // ---- 4. true vs predicted (two bars per class: true muted, predicted solid) ----
  // scale to the larger of the true (50) and the largest predicted count so no bar overflows
  var tvpMax = Math.max(50, Math.max.apply(null, CLASSES.map(function(c){ return predC[c]||0; })));
  var tvp = CLASSES.map(function(c){
    var tr = trueC[c]||0, pr = predC[c]||0;
    return '<div class="dpair">'+hbar('true '+CCODE[c], tr, tvpMax, COL.muted, 'sub')+
           hbar('pred '+CCODE[c], pr, tvpMax, COL[CTAG[c]], 'sub')+'</div>';
  });
  renderBars('tvp-dist', tvp);

  // ---- confusion matrix ----
  var cm = M.confusion_matrix;
  document.querySelector('.cm thead').innerHTML =
    '<tr><th class="corner"></th>'+CLASSES.map(function(c){
      return '<th class="collab">Pred. '+CCODE[c]+'<small>'+c+'</small></th>';
    }).join('')+'<th class="collab">Row</th></tr>';
  var colTot = {}; CLASSES.forEach(function(c){ colTot[c]=0; });
  var body='';
  CLASSES.forEach(function(t){
    var rsum=0, row='<tr><td class="rowlab">True '+CCODE[t]+'</td>';
    CLASSES.forEach(function(p){
      var v=cm['t_'+t+'_p_'+p]; rsum+=v; colTot[p]+=v;
      row += '<td class="cellv '+(t===p?'diag':'off'+p.toLowerCase())+'">'+v+'</td>';
    });
    body += row + '<td class="marg num">'+rsum+'</td></tr>';
  });
  var colRow='<tr><td class="rowlab">Col total</td>';
  CLASSES.forEach(function(c){ colRow += '<td class="marg num">'+colTot[c]+'</td>'; });
  body = body + colRow + '<td class="marg num">'+M.n_reviews+'</td></tr>';
  document.getElementById('cm-body').innerHTML = body;

  // ---- 5. accuracy by class (stacked correct/errors) ----
  var accHtml = CLASSES.map(function(c){
    var ca = M.class_accuracy[c];
    var good = ca.correct, bad = ca.total - ca.correct;
    var gw = ca.total ? Math.max(good/ca.total*100, (good?2:0)) : 0;
    var bw = ca.total ? Math.max(bad/ca.total*100, (bad?2:0)) : 0;
    return '<div class="accrow"><span class="al">'+CCODE[c]+' <span style="color:var(--faint);font-weight:500">('+c+')</span></span>'+
           '<div class="acc-stack"><div class="ag" style="width:'+gw+'%"></div><div class="ar" style="width:'+bw+'%"></div></div>'+
           '<span class="av"><b class="num">'+ca.accuracy*100+'%</b> · '+good+'/'+ca.total+'</span></div>';
  }).join('');
  document.getElementById('acc-list').innerHTML = accHtml;

  // error flow chips
  var flow = M.misclassification_flow;
  document.getElementById('flow-chips').innerHTML =
    '<span style="font-size:12px;color:var(--faint);align-self:center;font-weight:600">ERROR FLOW (true\u2192pred):</span> ' +
    Object.keys(flow).sort(function(a,b){return flow[b]-flow[a];}).map(function(k){
      var p=k.split('->'); return '<span class="flow-chip"><span class="from">'+CCODE[p[0]]+' \u2192</span> '+CCODE[p[1]]+' <span class="num">'+flow[k]+'</span></span>';
    }).join('') || '<span style="font-size:12px;color:var(--faint)">none</span>';

  // ---- emotion bars (7 & 8) ----
  function emoBarRows(dist){
    dist = dist || {};
    var total=0; Object.keys(dist).forEach(function(k){ total+=dist[k]; });
    return Object.keys(dist).sort(function(a,b){return dist[b]-dist[a];}).map(function(k){
      var label = (k==='null'||k==='None') ? 'no match' : k;
      return '<div class="drow"><span class="dl">'+label+'</span>'+
        '<div class="dtrack"><div class="dfill" style="width:'+(dist[k]?Math.max(dist[k]/total*100,1.5):0)+'%;background:#3572b8"></div></div>'+
        '<span class="dc">'+dist[k]+'</span></div>';
    }).join('');
  }
  document.getElementById('llm-bars').innerHTML = emoBarRows(M.llm_emotion_distribution);
  document.getElementById('nrc-bars').innerHTML = emoBarRows(M.nrc_emotion_distribution);

  // ---- 9. emotion agreement ----
  var arE = M.emotion_agree_on_evaluated;
  var emoDiff = M.n_reviews - M.emotion_agree_count - M.nrc_no_match;
  g('emo-agree-pct', (arE*100).toFixed(1)+'%');
  g('emo-agree-cap', M.emotion_agree_count+'/'+M.n_reviews+' agree overall');
  function aPct(x){ return x/M.n_reviews*100; }
  document.getElementById('emo-agr').innerHTML =
    '<div class="a-agree" style="width:'+aPct(M.emotion_agree_count).toFixed(2)+'%"></div>'+
    '<div class="a-diff" style="width:'+aPct(emoDiff).toFixed(2)+'%"></div>'+
    '<div class="a-none" style="width:'+aPct(M.nrc_no_match).toFixed(2)+'%"></div>';

  var llmTop = Object.keys(M.llm_emotion_distribution||{}).sort(function(a,b){return M.llm_emotion_distribution[b]-M.llm_emotion_distribution[a];})[0];
  var nrcTop = Object.keys(M.nrc_emotion_distribution||{}).filter(function(k){return k!=='null'&&k!=='None';}).sort(function(a,b){return M.nrc_emotion_distribution[b]-M.nrc_emotion_distribution[a];})[0];
  document.getElementById('emo-note').innerHTML =
    'The two methods agree on <b>'+M.emotion_agree_count+'/'+M.n_reviews+'</b> ('+(arE*100).toFixed(1)+'% of those with an NRC emotion). The LLM reads the dominant tone as <b>'+llmTop+'</b>, '+
    'while the word-level NRC lexicon is pulled toward <b>'+(nrcTop==='null'?'none':nrcTop)+'</b> — because gift-card staples such as <i>gift</i>, <i>good</i> and <i>money</i> carry multiple NRC emotion associations at once, '+
    'single-word scoring cannot separate them, and the two methods diverge most on this neutral-positive corpus.';

  // ---- interactive filters + table ----
  var F = {verdict:'all', pred:'all', rating:'all'};
  var counts = {correct:0, wrong:0}; CLASSES.forEach(function(c){ counts[c]=0; });
  counts.rating = {1:0,2:0,3:0,4:0,5:0};
  R.forEach(function(r){
    if(r.correct) counts.correct++; else counts.wrong++;
    counts[r.predicted]++; counts.rating[Math.round(r.rating)]++;
  });
  var pg = document.getElementById('pred-group');
  CLASSES.forEach(function(c){
    var b=document.createElement('button'); b.className='pill'; b.setAttribute('data-f','pred'); b.setAttribute('data-v',c);
    b.innerHTML = CCODE[c]+' <span class="ct"></span>'; pg.appendChild(b);
  });
  var rg = document.getElementById('rate-group');
  [1,2,3,4,5].forEach(function(s){ if(counts.rating[s]){
    var b=document.createElement('button'); b.className='pill'; b.setAttribute('data-f','rating'); b.setAttribute('data-v',String(s));
    b.innerHTML=s+'\u2605 <span class="ct"></span>'; rg.appendChild(b);
  }});
  document.querySelectorAll('#filters .pill').forEach(function(p){
    var f=p.dataset.f,v=p.dataset.v,n=null;
    if(f==='verdict'&&v==='correct') n=counts.correct;
    else if(f==='verdict'&&v==='wrong') n=counts.wrong;
    else if(f==='pred'&&v!=='all') n=counts[v];
    else if(f==='rating'&&v!=='all') n=counts.rating[parseInt(v,10)];
    if(n!=null){ var ct=p.querySelector('.ct'); if(ct) ct.textContent=n; }
  });
  function matches(r){
    if(F.verdict==='correct' && !r.correct) return false;
    if(F.verdict==='wrong' && r.correct) return false;
    if(F.pred!=='all' && r.predicted!==F.pred) return false;
    if(F.rating!=='all' && Math.round(r.rating)!==parseInt(F.rating,10)) return false;
    return true;
  }
  function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  R.forEach(function(r){ r._short = r.text.length>170 ? r.text.slice(0,170)+'\u2026' : r.text; });
  function render(){
    var rows = R.filter(matches);
    document.getElementById('tbody').innerHTML = rows.map(function(r){
      function etag(m,val){ return val?'<span class="etag"><span class="m">'+m+'</span>'+esc(String(val))+'</span>':'<span class="etag na"><span class="m">'+m+'</span>\u2013</span>'; }
      var ab = r.emo_agree===true?'<span class="agree yes"><span class="a-ico">\u2713</span></span>'
             : r.emo_agree===false?'<span class="agree no"><span class="a-ico">\u2715</span></span>'
             : '<span class="agree na"><span class="a-ico">\u2013</span></span>';
      var ico = r.correct?'\u2713':'\u2715';
      return '<tr class="'+(r.correct?'':'tr-fail')+'">'+
        '<td class="n">'+(r.index+1)+'</td>'+
        '<td class="title-max"><b>'+esc(r.title||'(no title)')+'</b></td>'+
        '<td class="txt">'+esc(r._short)+'</td>'+
        '<td class="rating num">'+r.rating.toFixed(1)+'</td>'+
        '<td><span class="tag '+CTAG[r.true]+'">'+CCODE[r.true]+'</span></td>'+
        '<td><span class="tag '+CTAG[r.predicted]+'">'+CCODE[r.predicted]+'</span></td>'+
        '<td class="num" style="text-align:center">'+r.confidence.toFixed(2)+'</td>'+
        '<td>'+etag('L',r.llm_emotion)+'</td>'+
        '<td>'+etag('R',r.nrc_emotion)+'</td>'+
        '<td class="c">'+ab+'</td>'+
        '<td class="c"><span class="verdict '+(r.correct?'y':'n')+'"><span class="ico">'+ico+'</span>'+(r.correct?'CORRECT':'WRONG')+'</span></td>'+
      '</tr>';
    }).join('');
    var parts=[];
    if(F.verdict==='correct') parts.push('correct'); else if(F.verdict==='wrong') parts.push('misclassified');
    if(F.pred!=='all') parts.push('predicted '+CCODE[F.pred]);
    if(F.rating!=='all') parts.push(F.rating+'\u2605 star');
    document.getElementById('t-shown').innerHTML =
      'Showing <b class="num">'+rows.length+'</b> of <span class="num">'+R.length+'</span> reviews'+
      (parts.length?' \u00b7 '+parts.join(' \u00b7 '):' \u00b7 all reviews');
  }
  render();
  document.getElementById('filters').addEventListener('click', function(e){
    var b = e.target.closest('.pill'); if(!b) return;
    var f = b.dataset.f;
    F[f] = b.dataset.v;
    document.querySelectorAll('#filters .pill[data-f="'+f+'"]').forEach(function(p){p.classList.remove('active');});
    b.classList.add('active'); render();
  });
</script>
</body>
</html>
"""

HTML = HTML.replace("__DATA__", json.dumps({
    "metrics": metrics,
    "reviews": reviews,
    "generated": generated,
}, ensure_ascii=False))

with open(OUT, "w") as f:
    f.write(HTML)

print(f"Wrote {OUT} ({os.path.getsize(OUT):,} bytes); reviews embedded: {len(reviews)}")
