"""Create an unfilled human review form; never adjudicate on a human's behalf."""
import argparse,hashlib,json
from pathlib import Path
from reviewer import ROOT,load_case,validate

def template(case,actual):
    d=load_case(case);actual=Path(actual);validate(json.loads(actual.read_text()),d)
    expected=ROOT/'evals/golden'/case/'expected.json';e=json.loads(expected.read_text())
    return {'reviewer_kind':'human','reviewer':'','actual_sha256':hashlib.sha256(actual.read_bytes()).hexdigest(),'expected_sha256':hashlib.sha256(expected.read_bytes()).hexdigest(),'criteria':[{'id':i+1,'criterion':s,'passed':None,'reason':''} for i,s in enumerate(e['rubric']['criteria'])]}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--actual',required=True);p.add_argument('--out',required=True);a=p.parse_args();result=template(a.case,a.actual)
    with Path(a.out).open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
