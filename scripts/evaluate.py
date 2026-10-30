"""Mechanical checks plus separately recorded human semantic adjudication."""
import argparse,json,hashlib,re,sys
from pathlib import Path
from reviewer import ROOT,load_case,validate

def baseline(d):
    if not d['files']:return 'insufficient_context',[]
    t='\n'.join(d['files'].values());m=re.search(r'disable! date: "(\d{4}-\d{2}-\d{2})"',t)
    if m and m[1]<=d.get('cutoff','')[:10]:return 'no_action',[]
    return ('no_action',[]) if re.search(r'^  test do\s*$',t,re.M) else ('findings',['missing_test'])

def evaluate(actual_root=None):
    frozen=json.loads((ROOT/'evals/freeze-v2.json').read_text())
    for path,h in frozen.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=h:raise ValueError('frozen case changed: '+path)
    rows=[]
    for case in json.loads((ROOT/'evals/manifest.json').read_text()):
        d=load_case(case);e=json.loads((ROOT/'evals/golden'/case/'expected.json').read_text())
        folder=Path(actual_root)/case if actual_root else ROOT/'evals/golden'/case
        path=folder/'actual.json';error=None;actual=None
        try:actual=validate(json.loads(path.read_text()),d)
        except Exception as exc:error=str(exc)
        cats=[f['category'] for f in actual['findings']] if actual else []
        required=e['required_categories']
        matched=bool(actual and actual['disposition']==e['disposition'] and sorted(set(cats))==sorted(set(required)))
        # A correct category/quote never implies semantic acceptance.
        semantic='pending';adjudication=folder/'adjudication.json'
        if adjudication.exists() and actual:
            a=json.loads(adjudication.read_text());checks=a.get('criteria',[])
            required_count=len(e['rubric']['criteria'])
            if (a.get('reviewer_kind')=='human' and a.get('reviewer','').strip() and a.get('actual_sha256')==hashlib.sha256(path.read_bytes()).hexdigest() and a.get('expected_sha256')==hashlib.sha256((ROOT/'evals/golden'/case/'expected.json').read_bytes()).hexdigest() and len(checks)==required_count and all(isinstance(c,dict) and c.get('id')==i+1 and c.get('criterion')==e['rubric']['criteria'][i] and type(c.get('passed'))==bool and isinstance(c.get('reason'),str) and c['reason'].strip() for i,c in enumerate(checks))):
                semantic='accepted' if all(c['passed'] for c in checks) else 'rejected'
        bd,bc=baseline(d)
        rows.append({'case_id':case,'schema_valid':actual is not None,'error':error,'expected':e['disposition'],'actual':actual['disposition'] if actual else None,'category_agreement':matched,'semantic_status':semantic,'baseline_category_agreement':bd==e['disposition'] and sorted(set(bc))==sorted(set(required))})
    return {'cases':rows,'total':len(rows),'schema_valid':sum(x['schema_valid'] for x in rows),'category_agreement':sum(x['category_agreement'] for x in rows),'baseline_category_agreement':sum(x['baseline_category_agreement'] for x in rows),'human_accepted':sum(x['semantic_status']=='accepted' for x in rows),'human_pending':sum(x['semantic_status']=='pending' for x in rows),'semantic_precision':None,'note':'Category agreement is diagnostic only. Human identity is a recorded attestation, not cryptographically authenticated; verify in code review.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--actual-root');p.add_argument('--out',default='evals/results.json');g=p.add_mutually_exclusive_group();g.add_argument('--mechanical-only',action='store_true');g.add_argument('--drift-only',action='store_true');a=p.parse_args();r=evaluate(a.actual_root);o=Path(a.out);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='cases'},indent=2));sys.exit(0 if (r['schema_valid']==r['total'] and (a.mechanical_only or (a.drift_only and r['category_agreement']==r['total']) or (not a.drift_only and r['human_accepted']==r['total']))) else 1)
