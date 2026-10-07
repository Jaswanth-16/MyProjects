"""Dependency-free, offline reporting. All values are derived from SQL exports."""

from html import escape
import json


def preview_svg(kpis, daily, routes):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="640" viewBox="0 0 1120 640" role="img" aria-labelledby="title desc">',
             '<title id="title">TransitPulse synthetic transit analytics</title>',
             '<desc id="desc">KPI cards and on-time performance by route, calculated from the reproducible demonstration.</desc>',
             '<rect width="1120" height="640" rx="22" fill="#101c2c"/>',
             '<g font-family="Arial,sans-serif" fill="#e9f1fb">',
             '<text x="42" y="58" font-size="15" fill="#59dac3" letter-spacing="3">DATA ENGINEERING / TRANSIT OPERATIONS</text>',
             '<text x="42" y="110" font-size="42" font-weight="bold">TransitPulse</text>',
             '<text x="42" y="143" font-size="16" fill="#a9bdd4">Incremental ingestion. Trusted metrics. Reproducible results.</text>']
    cards = [('Scheduled trips', f"{kpis['scheduled_trips']:,}"),
             ('On-time arrivals', f"{kpis['on_time_pct'] or 0:.2f}%"),
             ('Passengers', f"{kpis['passengers']:,}"),
             ('Cancellation rate', f"{kpis['cancellation_pct'] or 0:.2f}%")]
    for i, (label, value) in enumerate(cards):
        x = 42 + i * 260
        parts += [f'<rect x="{x}" y="178" width="244" height="110" rx="12" fill="#1b2c43"/>',
                  f'<text x="{x+18}" y="208" font-size="14" fill="#a9bdd4">{label}</text>',
                  f'<text x="{x+18}" y="255" font-size="34" font-weight="bold">{value}</text>']
    parts.append('<text x="42" y="333" font-size="20" font-weight="bold">On-time performance by route</text>')
    for i, route in enumerate(routes):
        rows = [d for d in daily if d['route_id'] == route['route_id']]
        completed = sum(d['completed_trips'] for d in rows)
        pct = 100 * sum(d['on_time_trips'] for d in rows) / completed if completed else 0
        y = 358 + i * 35
        parts += [f'<text x="42" y="{y+16}" font-size="15">{escape(route["route_name"])}</text>',
                  f'<rect x="255" y="{y}" width="675" height="22" rx="5" fill="#263a53"/>',
                  f'<rect x="255" y="{y}" width="{pct*6.75:.1f}" height="22" rx="5" fill="#59dac3"/>',
                  f'<text x="950" y="{y+17}" font-size="16">{pct:.2f}%</text>']
    parts += ['<text x="42" y="615" font-size="13" fill="#a9bdd4">SYNTHETIC DATA | Completed-trip denominator | On time = arrival delay &lt;= 5 minutes</text>', '</g></svg>']
    return '\n'.join(parts)


def dashboard_html(daily, routes):
    payload = json.dumps(dict(daily=daily, routes=routes)).replace('<', '\\u003c').replace('&', '\\u0026')
    template = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TransitPulse | Operations overview</title><style>
:root{font-family:Inter,Segoe UI,Arial,sans-serif;color:#e9f1fb;background:#101c2c;color-scheme:dark}
body{margin:0}main{max-width:1200px;margin:auto;padding:40px 28px}.eyebrow{font-size:12px;letter-spacing:3px;color:#59dac3}
h1{font-size:46px;letter-spacing:-2px;margin:18px 0 8px}p{color:#a9bdd4;line-height:1.6}.filters{display:flex;gap:20px;flex-wrap:wrap;margin:28px 0}
label{display:grid;gap:8px;font-size:13px;color:#a9bdd4}select,input{padding:10px 14px;background:#1b2c43;border:1px solid #39506a;border-radius:7px;color:#e9f1fb}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.card,.panel{padding:22px;background:#1b2c43;border:1px solid #294058;border-radius:14px}.card span{font-size:13px;color:#a9bdd4}.card strong{display:block;font-size:32px;margin-top:12px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px}h2{font-size:18px;margin:0 0 24px}.bar-row{display:grid;grid-template-columns:155px 1fr 62px;gap:10px;align-items:center;margin:18px 0;font-size:13px}.track{height:12px;background:#30445e;border-radius:5px}.fill{height:100%;background:#59dac3;border-radius:5px}.value{text-align:right}.table-wrap{overflow:auto;margin-top:20px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:13px 12px;text-align:right;border-bottom:1px solid #30445e}th:first-child,td:first-child{text-align:left}th{color:#a9bdd4;font-weight:500}footer{font-size:12px;color:#a9bdd4;margin-top:24px}.empty{color:#a9bdd4}
@media(max-width:850px){.cards{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.bar-row{grid-template-columns:130px 1fr 55px}h1{font-size:36px}}
</style></head><body><main>
<div class="eyebrow">TRANSIT OPERATIONS / SYNTHETIC DEMO</div><h1>TransitPulse</h1>
<p>A reproducible view of service reliability, passenger demand and revenue.</p>
<div class="filters"><label>Depot<select id="depot"><option value="">All depots</option><option>North</option><option>South</option></select></label><label>From<input type="date" id="from"></label><label>To<input type="date" id="to"></label></div>
<div class="cards" id="cards" aria-live="polite"></div>
<div class="grid"><section class="panel"><h2>On-time performance by route</h2><div id="bars"></div></section><section class="panel"><h2>Service mix and utilisation</h2><div id="mix"></div></section></div>
<section class="panel table-wrap"><h2>Route scorecard</h2><table><thead><tr><th>Route</th><th>Trips</th><th>Completed</th><th>On time</th><th>Passengers</th><th>Revenue (INR)</th></tr></thead><tbody id="table"></tbody></table></section>
<footer>Fictional routes and synthetic trips. On time: arrival delay &le; 5 minutes, among completed trips. Load factor: passengers / capacity of completed trips. All dates are UTC. This HTML preview is separate from Power BI.</footer>
</main><script type="application/json" id="data">__PAYLOAD__</script><script>
const data=JSON.parse(document.getElementById('data').textContent);const byId=id=>document.getElementById(id);
const num=n=>new Intl.NumberFormat('en-IN',{maximumFractionDigits:2}).format(n);const pct=(n,d)=>d?(100*n/d).toFixed(2)+'%':'N/A';
function sum(rows,key){return rows.reduce((a,r)=>a+r[key],0)}
function node(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n}
function render(){const rows=data.daily.filter(r=>(!byId('depot').value||r.depot===byId('depot').value)&&(!byId('from').value||r.service_date>=byId('from').value)&&(!byId('to').value||r.service_date<=byId('to').value));
const total=sum(rows,'scheduled_trips'),completed=sum(rows,'completed_trips');byId('cards').replaceChildren();
[['Scheduled trips',num(total)],['On-time arrivals',pct(sum(rows,'on_time_trips'),completed)],['Passengers',num(sum(rows,'passengers'))],['Revenue (INR)',num(sum(rows,'revenue_paise')/100)]].forEach(([label,value])=>{const c=node('div',undefined,'card');c.append(node('span',label),node('strong',value));byId('cards').append(c)});
byId('bars').replaceChildren();byId('table').replaceChildren();
for(const route of data.routes){const rr=rows.filter(r=>r.route_id===route.route_id),n=sum(rr,'scheduled_trips');if(!n)continue;const done=sum(rr,'completed_trips'),on=sum(rr,'on_time_trips');const bar=node('div',undefined,'bar-row'),track=node('div',undefined,'track'),fill=node('div',undefined,'fill');fill.style.width=(done?100*on/done:0)+'%';track.append(fill);bar.append(node('span',route.route_name),track,node('span',pct(on,done),'value'));byId('bars').append(bar);const tr=node('tr');[route.route_name,num(n),num(done),pct(on,done),num(sum(rr,'passengers')),num(sum(rr,'revenue_paise')/100)].forEach(v=>tr.append(node('td',v)));byId('table').append(tr)}
byId('mix').replaceChildren();[['Completed trips',num(completed)],['Cancelled trips',num(sum(rows,'cancelled_trips'))],['Cancellation rate',pct(sum(rows,'cancelled_trips'),total)],['Load factor',pct(sum(rows,'passengers'),sum(rows,'completed_capacity'))],['Average arrival delay',completed?(sum(rows,'total_delay_minutes')/completed).toFixed(2)+' min':'N/A']].forEach(([label,value])=>{const p=node('p');p.textContent=label+': '+value;byId('mix').append(p)});if(!total)byId('bars').append(node('p','No trips match these filters.','empty'));}
for(const id of ['depot','from','to'])byId(id).addEventListener('change',render);render();
</script></body></html>'''
    return template.replace('__PAYLOAD__', payload)
