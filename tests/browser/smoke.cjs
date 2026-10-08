'use strict';
const {chromium,expect}=require('@playwright/test');
const {spawn,spawnSync}=require('node:child_process');
const {mkdtempSync,readFileSync,rmSync}=require('node:fs');
const {tmpdir}=require('node:os');const path=require('node:path');
const root=path.resolve(__dirname,'../..'),python=process.env.PYTHON||'python';
const processes=[],results=[];let browser;const workspace=mkdtempSync(path.join(tmpdir(),'portfolio-browser-'));
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function server(project,port){
 const child=spawn(python,['-m',project,'serve','--port',String(port)],{cwd:path.join(root,project),stdio:['ignore','pipe','pipe']});processes.push(child);
 for(let i=0;i<100;i++){if(child.exitCode!==null)throw Error(project+' server exited');try{if((await fetch('http://127.0.0.1:'+port)).ok)return;}catch{}await delay(100);}
 throw Error(project+' server did not start');
}
async function check(name,fn){await fn();results.push({name,pass:true});console.log('PASS '+name);}
(async()=>{
 try{
  const demo=spawnSync(python,['-m','transitpulse','demo','--workspace',path.join(workspace,'transit'),'--count','1000'],{cwd:path.join(root,'transitpulse'),encoding:'utf8'});
  if(demo.status!==0)throw Error('TransitPulse fixture generation failed: '+demo.stderr);
  const exports=JSON.parse(demo.stdout).exports;
  await Promise.all([server('pipelinecopilot',8765),server('loglens',8766),server('opsevidence',8767)]);
  browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.CHROMIUM_EXECUTABLE_PATH}:{}),args:JSON.parse(process.env.CHROMIUM_EXTRA_ARGS||'[]')});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await check('TransitPulse dashboard agrees with source data',async()=>{
   await page.goto('file://'+path.join(exports,'dashboard.html'));
   const total=await page.locator('#data').evaluate(e=>JSON.parse(e.textContent).daily.reduce((s,r)=>s+r.scheduled_trips,0));
   await expect(page.locator('#cards .card').first().locator('strong')).toHaveText(new Intl.NumberFormat('en-IN').format(total));
   await expect(page.locator('#table tr')).toHaveCount(6);
  });
  await check('TransitPulse depot and date filters',async()=>{
   await page.selectOption('#depot','North');
   const expected=await page.locator('#data').evaluate(e=>JSON.parse(e.textContent).daily.filter(r=>r.depot==='North').reduce((s,r)=>s+r.scheduled_trips,0));
   await expect(page.locator('#cards .card').first().locator('strong')).toHaveText(new Intl.NumberFormat('en-IN').format(expected));
   await page.locator('#from').fill('2030-01-01');await page.locator('#from').dispatchEvent('change');
   await expect(page.locator('#bars')).toContainText('No trips match');await expect(page.locator('#cards')).toContainText('N/A');
  });
  await check('PipelineCopilot supported sample and source links',async()=>{
   await page.goto('http://127.0.0.1:8765');await page.locator('[data-sample="storage"]').click();await page.locator('#ask').click();
   await expect(page.locator('#meta')).toContainText('SUPPORTED');await expect(page.locator('#citations a').first()).toHaveAttribute('href',/^https:\/\/learn\.microsoft\.com\//);
  });
  await check('PipelineCopilot unknown question abstains',async()=>{
   await page.locator('[data-sample="unknown"]').click();await page.locator('#ask').click();
   await expect(page.locator('#meta')).toContainText('INSUFFICIENT EVIDENCE');await expect(page.locator('#citations a')).toHaveCount(0);
  });
  await check('LogLens sample produces structured evidence',async()=>{
   await page.goto('http://127.0.0.1:8766');await expect(page.locator('#provider')).toContainText('offline');await page.locator('#run').click();
   await expect(page.locator('#status')).toContainText('VALIDATED');const out=JSON.parse(await page.locator('#result').textContent());
   expect(out.error_code).toBe('AuthorizationPermissionMismatch');expect(out.evidence.length).toBeGreaterThan(0);
  });
  await check('LogLens unknown and invalid input states',async()=>{
   await page.locator('[data-example="unknown"]').click();await page.locator('#run').click();await expect(page.locator('#result')).toContainText('"category": "unknown"');
   await page.locator('#log').fill('');await page.locator('#run').click();await expect(page.locator('#status')).toHaveText('REQUEST FAILED');await expect(page.locator('#run')).toBeEnabled();
  });
  await check('LogLens treats HTML as text',async()=>{
   await page.locator('#log').fill('pipeline: demo\nSqlTimeout <img src=x onerror="window.injected=true">');await page.locator('#run').click();
   await expect(page.locator('#status')).toContainText('VALIDATED');await expect(page.locator('#result')).toContainText('<img');expect(await page.evaluate(()=>Boolean(window.injected))).toBe(false);await expect(page.locator('#result img')).toHaveCount(0);
  });
  await check('OpsEvidence loads incidents, tools and citations',async()=>{
   await page.goto('http://127.0.0.1:8767');await expect(page.locator('#incident option')).toHaveCount(15);await page.selectOption('#incident','run-0420');await page.locator('#run').click();
   await expect(page.locator('#status')).toContainText('supported');await expect(page.locator('#trace .step')).toHaveCount(3);
   const out=JSON.parse(await page.locator('#result').textContent());expect(out.evidence.some(e=>e.kind==='runbook')).toBe(true);expect(out.metrics.live_data_tool_calls).toBe(0);
  });
  await check('OpsEvidence changes selected incident',async()=>{
   await page.selectOption('#incident','run-0408');await page.locator('#run').click();await expect(page.locator('#result')).toContainText('AuthorizationPermissionMismatch');
  });
  await check('OpsEvidence recovers after invalid question',async()=>{
   await page.locator('#question').fill('');await page.locator('#run').click();await expect(page.locator('#status')).toHaveText('REQUEST FAILED');await expect(page.locator('#run')).toBeEnabled();
   await page.locator('#question').fill('What should I check?');await page.locator('#run').click();await expect(page.locator('#status')).toContainText('supported');
  });
  await check('AI interfaces fit a mobile viewport',async()=>{
   await page.setViewportSize({width:390,height:844});
   for(const port of [8765,8766,8767]){await page.goto('http://127.0.0.1:'+port);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);}
  });
  await check('No uncaught browser JavaScript errors',async()=>expect(errors).toEqual([]));
  console.log(JSON.stringify({status:'pass',tests:results.length,results},null,2));
 }catch(error){if(browser){const pages=browser.contexts().flatMap(c=>c.pages());for(const p of pages)console.error('UI failure:',await p.locator('#warning').textContent().catch(()=>''));}console.error(error);process.exitCode=1;}
 finally{if(browser)await browser.close();for(const p of processes)p.kill('SIGTERM');rmSync(workspace,{recursive:true,force:true});}
})();
