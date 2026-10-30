"""Prepare bounded formula evidence from immutable local commits; never check out/run PR code."""
import argparse,json,re,subprocess
from pathlib import Path
from reviewer import MAX_INPUT
SHA=re.compile(r'[0-9a-f]{40}')
FORMULA=re.compile(r'Formula/[a-z0-9]/[a-zA-Z0-9@+_.-]+\.rb')
def prepare(source,base,head,case_id):
    if not SHA.fullmatch(base) or not SHA.fullmatch(head):raise ValueError('full commit SHA required')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',case_id):raise ValueError('invalid case ID')
    def git(*args):return subprocess.check_output(['git','-C',str(source),*args],text=True,timeout=30)
    for sha in [base,head]:git('cat-file','-e',sha+'^{commit}')
    paths=git('diff','--name-only',base,head).splitlines()
    if not 1<=len(paths)<=5 or any(not FORMULA.fullmatch(p) for p in paths):raise ValueError('only 1–5 formula changes supported')
    files={}
    for path in paths:
        if int(git('cat-file','-s',head+':'+path))>64000:raise ValueError('formula size cap')
        files[path]=git('show',head+':'+path)
    d={'case_id':case_id,'kind':'sandbox_commit_review','base':base,'head':head,'cutoff':git('show','-s','--format=%cI',head).strip(),'files':files,'diff':git('diff','--no-ext-diff',base,head,'--',*paths),'scope':'Review the supplied formula snapshot and diff. Source builds and upstream implementation are not available.'}
    if len(json.dumps(d).encode())>MAX_INPUT:raise ValueError('input byte cap')
    return d
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--base',required=True);p.add_argument('--head',required=True);p.add_argument('--case-id',required=True);p.add_argument('--out',required=True);a=p.parse_args();d=prepare(a.source,a.base,a.head,a.case_id);o=Path(a.out);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(d,indent=2)+'\n')
