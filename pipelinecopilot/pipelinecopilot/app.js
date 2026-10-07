'use strict';
const el = id => document.getElementById(id);
const examples = {
 storage: ['Why did my copy activity fail?', 'AuthorizationPermissionMismatch: HTTP 403 forbidden copying to ADLS Gen2.'],
 schema: ['How do I investigate this schema change?', 'UserErrorInvalidColumnMappingColumnNotFound: source column trip_id is missing.'],
 throttle: ['What should I check before retrying?', 'HTTP 429 TooManyRequests: service rate limit reached.'],
 unknown: ['Explain quantum entanglement', '']
};
document.querySelectorAll('[data-sample]').forEach(button => button.addEventListener('click', () => {
 const [question, log] = examples[button.dataset.sample]; el('question').value = question; el('log').value = log;
}));
el('ask').addEventListener('click', async () => {
 el('ask').disabled = true; el('meta').textContent = 'RETRIEVING EVIDENCE'; el('warning').textContent = '';
 try {
  const response = await fetch('/api/ask', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:el('question').value,log:el('log').value})});
  const result = await response.json(); if (!response.ok) throw new Error(result.error || 'Request failed');
  el('summary').textContent = result.summary;
  el('meta').textContent = `${result.mode.toUpperCase()} · ${result.status.replaceAll('_',' ').toUpperCase()} · ${result.elapsed_ms} MS`;
  el('checks').replaceChildren(...result.checks.map(text => {const li=document.createElement('li');li.textContent=text;return li;}));
  el('citations').replaceChildren(...result.citations.map(source => {
   const div=document.createElement('div');div.className='source';const a=document.createElement('a');
   const url=new URL(source.url);if(url.protocol!=='https:' || url.hostname!=='learn.microsoft.com')throw new Error('Invalid source URL');
   a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';a.textContent=`[${source.id}] ${source.title} ↗`;div.append(a);return div;
  }));
  el('warning').textContent = result.warning || (result.status==='insufficient_evidence'?'The corpus does not support this question. No answer was invented.':'These checks are investigative guidance, not a confirmed root cause.');
 } catch(error) {el('meta').textContent='REQUEST FAILED';el('summary').textContent='Unable to investigate';el('checks').replaceChildren();el('citations').replaceChildren();el('warning').textContent=error.message;}
 finally {el('ask').disabled=false;}
});
