"""Scoped, read-only tools. The model never supplies SQL or file paths."""
import json
import sqlite3
import time
from datetime import datetime,timedelta
from pathlib import Path
from .contracts import obj,string,validate,ContractError
from .safety import scrub
from .retrieval import Index
DATA=Path(__file__).resolve().parent.parent/'data'

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'))

class Tools:
    def __init__(self,incident_id):
        rows=json.loads((DATA/'runs.json').read_text())
        self.db=sqlite3.connect(':memory:')
        self.db.row_factory=sqlite3.Row
        self.db.execute('CREATE TABLE runs (id TEXT PRIMARY KEY,pipeline TEXT,activity TEXT,started_at TEXT,status TEXT,duration_seconds INTEGER,error_code TEXT,message TEXT)')
        self.db.executemany('INSERT INTO runs VALUES (:id,:pipeline,:activity,:started_at,:status,:duration_seconds,:error_code,:message)',rows)
        self.db.commit();self.db.execute('PRAGMA query_only=ON')
        self.incident=self.db.execute('SELECT * FROM runs WHERE id=?',(incident_id,)).fetchone()
        if not self.incident or self.incident['status']!='Failed':
            self.db.close();raise ContractError('Choose an existing failed synthetic run')
        self.incident_id=incident_id
        self.index=Index(json.loads((DATA/'runbooks.json').read_text()))
        self.evidence={};self.trace=[]

    def close(self):self.db.close()

    def specs(self):
        return [
            {'name':'get_run','description':'Read the selected incident only. Other IDs are rejected.','schema':obj({'run_id':{'type':'string','enum':[self.incident_id]}})},
            {'name':'pipeline_stats','description':'Get failure counts and durations for the selected pipeline over 1-28 UTC calendar days ending at the incident.','schema':obj({'days':{'type':'integer','minimum':1,'maximum':28}})},
            {'name':'search_runbooks','description':'Retrieve up to three curated runbooks by symptoms or exact error code. Use the incident error code.','schema':obj({'query':string(500)})}
        ]

    def evidence_record(self,key,kind,value,source_url=None):
        content=canonical(scrub(value)) if not isinstance(value,str) else scrub(value)
        record={'id':key,'kind':kind,'content':content,'source_url':source_url}
        self.evidence[key]=record
        return record

    def call(self,name,arguments):
        start=time.perf_counter();status='ok'
        try:
            spec=next((s for s in self.specs()if s['name']==name),None)
            if spec is None:raise ContractError('Unknown read-only tool')
            validate(arguments,spec['schema'])
            if name=='get_run':
                result={'evidence':[self.evidence_record('RUN-'+self.incident_id,'run',dict(self.incident))]}
            elif name=='pipeline_stats':
                days=arguments['days'];anchor=datetime.fromisoformat(self.incident['started_at'].replace('Z','+00:00'))
                lower=(anchor-timedelta(days=days-1)).date().isoformat()+'T00:00:00Z'
                row=self.db.execute('SELECT COUNT(*) AS total_runs,SUM(status=?) AS failed_runs,ROUND(AVG(duration_seconds),2) AS avg_duration_seconds FROM runs WHERE pipeline=? AND started_at>=? AND started_at<=?',('Failed',self.incident['pipeline'],lower,self.incident['started_at'])).fetchone()
                stats={**dict(row),'pipeline':self.incident['pipeline'],'days':days,'window_start':lower,'window_end':self.incident['started_at']}
                stats['failure_rate_pct']=round(100*stats['failed_runs']/stats['total_runs'],2) if stats['total_runs'] else None
                result={'evidence':[self.evidence_record('STAT-'+self.incident['pipeline']+'-'+str(days),'statistics',stats)]}
            else:
                hits=self.index.search(arguments['query'])
                matched=[h for h in hits if h['matched_codes'] or h['score']>=3.5]
                records=[]
                for hit in matched:
                    d=hit['document'];content=d['title']+'\n'+d['symptoms']+'\n'+'\n'.join(d['checks'])
                    records.append(self.evidence_record('DOC-'+d['id'],'runbook',content,d['source_url']))
                result={'evidence':records,'note':'Lexical retrieval score is not confidence; review relevance.'}
        except ContractError as exc:
            status='rejected';result={'error':str(exc)}
        self.trace.append({'tool':name,'arguments':scrub(arguments),'status':status,'elapsed_ms':round((time.perf_counter()-start)*1000,2)})
        return result

    @staticmethod
    def incidents():
        rows=json.loads((DATA/'runs.json').read_text())
        return [{'id':r['id'],'pipeline':r['pipeline'],'error_code':r['error_code']}for r in sorted(rows,key=lambda r:(r['started_at'],r['id'])) if r['status']=='Failed'][-15:][::-1]
