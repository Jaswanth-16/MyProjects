"""Read-only ADF status evidence; never deploys, starts runs or fetches secrets."""
import argparse,json,subprocess
from datetime import datetime,timezone
from pathlib import Path

def collect(group,factory,run_ids,runner=subprocess.run):
    if not run_ids or len(set(run_ids))!=len(run_ids):raise ValueError('Supply distinct existing run IDs')
    records=[]
    for run_id in run_ids:
        args=['az','datafactory','pipeline-run','show','--resource-group',group,'--factory-name',factory,'--run-id',run_id,'--query','{status:status,pipeline:pipelineName,started:runStart,ended:runEnd}','--output','json','--only-show-errors']
        r=runner(args,check=False,capture_output=True,text=True)
        if r.returncode:raise RuntimeError('Azure read failed')
        row=json.loads(r.stdout)
        if not isinstance(row,dict) or set(row)!={'status','pipeline','started','ended'}:raise ValueError('Unexpected response')
        records.append({'sequence':len(records)+1,**row})
    passed=all(r['status']=='Succeeded' and r['pipeline']=='pl_transitpulse' for r in records)
    return {'captured_at':datetime.now(timezone.utc).isoformat(),'scope':'ADF status only. Verify activity outputs, snapshot reconciliation and replay separately.','status':'pass' if passed else 'fail','runs':records}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ['resource-group','factory','output']:p.add_argument('--'+arg,required=True)
    p.add_argument('--run-id',action='append',required=True);a=p.parse_args()
    try:
        report=collect(a.resource_group,a.factory,a.run_id)
        Path(a.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'captured_runs':len(report['runs'])}));return 0 if report['status']=='pass' else 1
    except (ValueError,RuntimeError,OSError):
        print(json.dumps({'status':'blocked','reason':'Check Azure login, permissions, run IDs, response and output path.'}));return 2
if __name__=='__main__':raise SystemExit(main())
