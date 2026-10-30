"""Export only configuration and one input. No expected answers or siblings."""
import argparse,json,hashlib
from pathlib import Path
from reviewer import ROOT,load_case,build_prompt

def prepare(case,out):
    d=load_case(case);d['case_id']='review'
    system,user,event=build_prompt(d)
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    files={'instructions.txt':system,'input.json':user+'\n'}
    for name,text in files.items():(out/name).write_text(text)
    hashes={name:hashlib.sha256(text.encode()).hexdigest() for name,text in files.items()}
    (out/'bundle.json').write_text(json.dumps({'files':hashes,'skill_sha256':event['sha256']},indent=2)+'\n')
    return hashes
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--out',required=True);a=p.parse_args();prepare(a.case,a.out)
