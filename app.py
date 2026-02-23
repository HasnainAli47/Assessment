import json, os, sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import SUMMARIES_FILE, MIN_INPUT_WORDS
from summarizer import summarize, InputTooShortError, NotHealthContentError
from evaluator import evaluate
from risk import compute_risk
from utils import (
    count_words, load_articles,
    save_summaries_json, save_evaluation_csv, ensure_dirs,
)

app = FastAPI(title="HEAL-Summ-Lite", version="1.0.0")
ensure_dirs()

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>HEAL-Summ-Lite</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:#f8f9fb;color:#222;line-height:1.55}
.wrap{max-width:980px;margin:0 auto;padding:2rem 1.2rem}

h1{font-size:1.5rem;font-weight:700;margin-bottom:.25rem}
.sub{color:#666;font-size:.9rem;margin-bottom:2rem}

.panel{background:#fff;border:1px solid #e0e3e8;border-radius:10px;
  padding:1.5rem;margin-bottom:1.4rem}
.panel h2{font-size:1rem;margin-bottom:.8rem}

.note{background:#f1f3f7;padding:.7rem 1rem;border-radius:6px;
  font-size:.85rem;color:#555;margin-bottom:1rem;border-left:3px solid #5b6abf}
.note code{background:#dde1ec;padding:1px 5px;border-radius:3px;font-size:.82rem}

btn{display:inline-flex;align-items:center;gap:.35rem;padding:.55rem 1.2rem;
  border:none;border-radius:7px;font-size:.88rem;font-weight:600;cursor:pointer}
.primary{background:#5b6abf;color:#fff}
.primary:hover{background:#4a59a8}
.primary:disabled{opacity:.5;cursor:wait}

.spin{display:none;width:15px;height:15px;border:2.5px solid #fff;
  border-top-color:transparent;border-radius:50%;animation:sp .55s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}

.msg{margin-top:.8rem;font-size:.88rem;color:#666}
.msg.err{color:#c0392b}

table{width:100%;border-collapse:collapse;font-size:.84rem;margin-top:1rem}
th{text-align:left;padding:.5rem .6rem;border-bottom:2px solid #e0e3e8;
  color:#888;font-size:.75rem;text-transform:uppercase;letter-spacing:.03em}
td{padding:.5rem .6rem;border-bottom:1px solid #eee;vertical-align:top}
tr:hover td{background:#fafbfd}

.tag{display:inline-block;padding:2px 8px;border-radius:99px;
  font-size:.72rem;font-weight:700;text-transform:uppercase}
.low{background:#e8f5e9;color:#2e7d32}
.med{background:#fff3e0;color:#e65100}
.hi{background:#ffebee;color:#c62828}

.sum{max-width:320px;font-size:.82rem;line-height:1.45}
.peek{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.more{color:#5b6abf;cursor:pointer;font-size:.78rem;font-weight:600;
  border:none;background:none;padding:0;margin-top:.25rem}

footer{text-align:center;color:#aaa;font-size:.78rem;margin-top:2rem}
</style>
</head>
<body>
<div class="wrap">
  <h1>HEAL-Summ-Lite</h1>
  <p class="sub">Local health-article summarizer with quality checks</p>

  <div class="panel">
    <h2>Batch processing</h2>
    <div class="note">
      Drop <code>.txt</code> articles into <code>data/raw_articles/</code>,
      then hit the button. Each file is summarised, evaluated, and risk-scored.
      Results are saved to <code>results/</code>.
    </div>
    <button class="primary" id="go" onclick="run()">
      <span class="spin" id="sp"></span>Process articles
    </button>
    <div class="msg" id="st"></div>
  </div>

  <div class="panel" id="out" style="display:none">
    <h2>Results</h2>
    <div id="tbl"></div>
  </div>

  <footer>HEAL-Summ-Lite &middot; runs locally &middot; nothing leaves your machine</footer>
</div>
<script>
function $(s){return document.querySelector(s)}

async function run(){
  var b=$('#go'),sp=$('#sp'),st=$('#st')
  b.disabled=true;sp.style.display='inline-block'
  st.textContent='Working…';st.className='msg'
  $('#out').style.display='none'
  try{
    var r=await fetch('/api/batch',{method:'POST'})
    if(!r.ok){var e=await r.json();throw new Error(e.error||r.statusText)}
    var d=await r.json()
    st.innerHTML='Processed <b>'+d.count+'</b> article(s).'
    show(d.records)
  }catch(e){st.textContent=e.message;st.className='msg err'}
  finally{b.disabled=false;sp.style.display='none'}
}

function show(rows){
  if(!rows||!rows.length)return
  $('#out').style.display=''
  var h='<table><thead><tr>'+
    '<th>Article</th><th>Summary</th><th>Words</th><th>Target</th><th>FKGL</th>'+
    '<th>Coverage</th><th>Missing&nbsp;#</th><th>Halluc.</th><th>Risk</th><th>Escalate</th>'+
    '</tr></thead><tbody>'
  rows.forEach(function(r,i){
    var c=r.risk_level==='Low'?'low':r.risk_level==='Medium'?'med':'hi'
    var s=r.summary||''
    var p=s.length>100?esc(s.slice(0,100))+'&hellip;':esc(s)
    h+='<tr><td><b>'+esc(r.article_id)+'</b></td>'+
      '<td class="sum"><div class="peek" id="p'+i+'">'+p+'</div>'+
      (s.length>100?'<button class="more" onclick="tog('+i+',this)" data-f="'+attr(s)+'">more</button>':'')+
      '</td>'+
      '<td>'+r.word_count+'</td><td>'+(r.target_range||'')+'</td><td>'+r.fkgl+'</td>'+
      '<td>'+(r.entity_coverage*100).toFixed(1)+'%</td>'+
      '<td>'+(r.missing_numbers?'Yes':'No')+'</td>'+
      '<td>'+(r.hallucination_flag?'Yes':'No')+'</td>'+
      '<td><span class="tag '+c+'">'+r.risk_level+'</span></td>'+
      '<td>'+(r.escalate?'Yes':'No')+'</td></tr>'
  })
  h+='</tbody></table>'
  $('#tbl').innerHTML=h
}

function tog(i,btn){
  var el=$('#p'+i)
  if(btn.textContent==='more'){
    el.textContent=btn.getAttribute('data-f')
    el.className='sum';btn.textContent='less'
  }else{
    var f=btn.getAttribute('data-f')
    el.innerHTML=f.length>100?esc(f.slice(0,100))+'&hellip;':esc(f)
    el.className='sum peek';btn.textContent='more'
  }
}
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML}
function attr(s){return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;')}
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return PAGE


@app.post("/api/summarize")
async def api_summarize(req: Request):
    body = await req.json()
    text = body.get("text", "").strip()
    if not text:
        return JSONResponse({"error": "No text provided."}, 400)
    if count_words(text) < MIN_INPUT_WORDS:
        return JSONResponse(
            {"error": f"Article too short — need at least {MIN_INPUT_WORDS} words."},
            422,
        )
    try:
        summ = summarize(text)
    except (InputTooShortError, NotHealthContentError) as exc:
        return JSONResponse({"error": str(exc)}, 422)

    evl = evaluate(text, summ["summary"])
    rsk = compute_risk(evl, summ["word_count"], summ["target_min"], summ["target_max"])
    rec = _record("interactive", summ, evl, rsk)
    _append(rec)
    return JSONResponse(rec)


@app.post("/api/batch")
async def api_batch():
    articles = load_articles()
    if not articles:
        return JSONResponse({"error": "No .txt files in data/raw_articles/"}, 404)

    records = []
    for art in articles:
        try:
            summ = summarize(art["text"])
        except (InputTooShortError, NotHealthContentError):
            continue
        evl = evaluate(art["text"], summ["summary"])
        rsk = compute_risk(evl, summ["word_count"], summ["target_min"], summ["target_max"])
        records.append(_record(art["id"], summ, evl, rsk))

    save_summaries_json(records)
    save_evaluation_csv(records)
    return JSONResponse({"count": len(records), "records": records})


@app.get("/api/results")
async def api_results():
    if not os.path.exists(SUMMARIES_FILE):
        return JSONResponse([])
    with open(SUMMARIES_FILE) as f:
        return JSONResponse(json.load(f))


def _record(aid, summ, evl, rsk):
    return {
        "article_id": aid,
        "summary": summ["summary"],
        "word_count": summ["word_count"],
        "target_range": f"{summ['target_min']}-{summ['target_max']}",
        "retries": summ["retries"],
        "fkgl": evl["fkgl"],
        "fre": evl["fre"],
        "entity_coverage": evl["entity_coverage"],
        "missing_numbers": evl["missing_numbers"],
        "hallucination_flag": evl["hallucination_flag"],
        "hallucinated_entities": evl["hallucinated_entities"],
        "risk_level": rsk["risk_level"],
        "escalate": rsk["escalate"],
    }


def _append(rec):
    records = []
    if os.path.exists(SUMMARIES_FILE):
        with open(SUMMARIES_FILE) as f:
            try:
                records = json.load(f)
            except json.JSONDecodeError:
                records = []
    records.append(rec)
    save_summaries_json(records)
