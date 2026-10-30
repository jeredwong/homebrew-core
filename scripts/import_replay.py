"""Import an actual assistant record. Never generate a decision from an oracle."""
import argparse,json,hashlib
from pathlib import Path
from reviewer import ROOT,load_case,build_prompt,validate

def ingest(case,bundle,record,out):
    bundle=Path(bundle);record=Path(record)
    d=load_case(case);neutral=dict(d,case_id='review');system,user,event=build_prompt(neutral)
    if (bundle/'instructions.txt').read_text()!=system or (bundle/'input.json').read_text()!=user+'\n':raise ValueError('bundle differs from frozen case/configuration')
    obj=json.loads(record.read_text());raw=obj['report'];validate(raw,neutral)
    if not isinstance(obj.get('observations'),str) or not obj['observations'].strip():raise ValueError('review observation required')
    target=Path(out)/case;target.mkdir(parents=True,exist_ok=False)
    (target/'assistant-record.json').write_bytes(record.read_bytes())
    report=dict(raw,case_id=case);validate(report,d)
    (target/'actual.json').write_text(json.dumps(report,indent=2)+'\n')
    transcript=[{'event':'provenance','engine':'fresh Codex subagent','requested_model':'gpt-6.1-sol','exact_backend_version':'unavailable','history':'none','isolation':'one exported input; filesystem tool restriction instructed, not OS-enforced','id_mapping':{'review':case}},event,{'role':'system','content':system},{'role':'user','content':user},{'role':'assistant','content':obj},{'event':'import','raw_record_sha256':hashlib.sha256(record.read_bytes()).hexdigest(),'note':'Normalized case_id only; report prose unchanged. Structured prompt/response record, not a raw provider/tool trace.'}]
    (target/'transcript.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in transcript))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--bundle',required=True);p.add_argument('--record',required=True);p.add_argument('--out',required=True);a=p.parse_args();ingest(a.case,a.bundle,a.record,a.out)
