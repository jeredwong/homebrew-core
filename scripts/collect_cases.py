"""Verify frozen source snapshots against Git, then export inputs and rubrics.
This preserves deliberate selection and frozen oracles; it never invents new labels.
"""
import argparse,json,subprocess,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def collect(source,out):
    out=Path(out)
    if out.exists() and any(out.iterdir()):raise ValueError('output must be empty')
    def git(*args):return subprocess.check_output(['git','-C',str(source),*args],text=True,timeout=30)
    frozen=json.loads((ROOT/'evals/freeze-v2.json').read_text())
    for path,digest in frozen.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('frozen file changed: '+path)
    cases=json.loads((ROOT/'evals/manifest.json').read_text())
    for case in cases:
        folder=ROOT/'evals/golden'/case;data=json.loads((folder/'input.json').read_text());head=data['head']
        for path,text in {**data['files'],**data.get('historical_guidance',{})}.items():
            if git('show',head+':'+path)!=text:raise ValueError('source differs: '+case+' '+path)
        # v2 additions omitted the diff's final newline; preserve the frozen bytes.
        if git('diff','--no-ext-diff',data['base'],head,'--',*data['files']).rstrip('\n')!=data['diff'].rstrip('\n'):raise ValueError('diff differs: '+case)
        if git('show','-s','--format=%cI',head).strip()!=data['cutoff']:raise ValueError('cutoff differs: '+case)
        target=out/'evals/golden'/case;target.mkdir(parents=True)
        for name in ['input.json','expected.json']:shutil.copyfile(folder/name,target/name)
    for name in ['manifest.json','freeze-v2.json','expectations.sha256']:shutil.copyfile(ROOT/'evals'/name,out/'evals'/name)
    return len(cases)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();print('Verified and exported',collect(a.source,a.out),'cases')
