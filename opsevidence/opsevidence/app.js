'use strict';
const el = id => document.getElementById(id);
async function setup(){
 const r=await fetch('/api/options');if(!r.ok)throw new Error('Unable to load options');const data=await r.json();
 el('provider').textContent=`Mode: ${data.provider} · ${data.provider==='offline'?'no model calls':'live provider calls enabled · check your plan limits'}`;
 if(data.incidents){for(const row of data.incidents){const o=document.createElement('option');o.value=row.id;o.textContent=`${row.id} · ${row.pipeline} · ${row.error_code}`;el('incident').append(o);}}
}
setup().catch(e=>{el('warning').textContent=e.message;el('run').disabled=true;});
const examples={storage:'Pipeline: bronze_trips\nActivity: CopyTrips\nErrorCode: AuthorizationPermissionMismatch\nMessage: HTTP 403 forbidden.',schema:'Pipeline: silver_metrics\nActivity: CopyMetrics\nErrorCode: UserErrorInvalidColumnMappingColumnNotFound\nMessage: CSV column passenger_count missing.',unknown:'Pipeline: mystery\nMessage: Unrecognised error needs investigation.'};
document.querySelectorAll('[data-example]').forEach(b=>b.addEventListener('click',()=>el('log').value=examples[b.dataset.example]));
el('run').addEventListener('click',async()=>{
 el('run').disabled=true;el('status').textContent='PROCESSING';el('warning').textContent='';el('result').textContent='';el('trace').replaceChildren();
 try{
 const payload=el('log')?{log:el('log').value}:{incident_id:el('incident').value,question:el('question').value};
 const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
 const data=await r.json();if(!r.ok)throw new Error(data.error||'Request failed');
 el('status').textContent=`${data.mode.toUpperCase()} · ${data.status||'VALIDATED'}`;el('warning').textContent=data.warning||'';
 el('headline').textContent=data.summary?.summary||data.answer?.assessment||'Validated result';
 for(const step of data.trace||[]){const d=document.createElement('div');d.className='step';d.textContent=`${step.tool} · ${step.status} · ${step.elapsed_ms} ms`;el('trace').append(d);}
 el('result').textContent=JSON.stringify(data.summary||{answer:data.answer,evidence:data.evidence,metrics:data.metrics},null,2);
 }catch(e){el('status').textContent='REQUEST FAILED';el('warning').textContent=e.message;}
 finally{el('run').disabled=false;}
});
