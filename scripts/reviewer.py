"""Trusted capability boundary: pure validation and prompt construction."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODEL="claude-sonnet-4-20250514"
MAX_INPUT=80000
MAX_REPORT=6000
CATEGORIES={"missing_test","test_coverage","dependency","platform","install"}
def digest(b): return hashlib.sha256(b).hexdigest()
def load_case(case_id):
    allowed=json.loads((ROOT/"evals/manifest.json").read_text())
    if case_id not in allowed: raise ValueError("case not in manifest")
    path=ROOT/"evals/golden"/case_id/"input.json"
    raw=path.read_bytes()
    if len(raw)>MAX_INPUT: raise ValueError("input byte cap")
    d=json.loads(raw)
    if d.get("case_id")!=case_id: raise ValueError("input ID mismatch")
    return d

def load_prepared(path):
    raw=Path(path).read_bytes()
    if len(raw)>MAX_INPUT:raise ValueError('input byte cap')
    d=json.loads(raw)
    if not isinstance(d,dict) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',d.get('case_id','')):raise ValueError('invalid case ID')
    if not isinstance(d.get('files'),dict) or not 1<=len(d['files'])<=5:raise ValueError('formula count')
    for path,text in d['files'].items():
        if not re.fullmatch(r'Formula/[a-z0-9]/[A-Za-z0-9@+_.-]+\.rb',path) or not isinstance(text,str):raise ValueError('invalid formula evidence')
    return d

def build_prompt(data):
    agents=(ROOT/"AGENTS.md").read_text()
    skill=(ROOT/".claude/skills/formula-review/SKILL.md").read_text()
    system=agents+"\n\n"+skill
    return system,json.dumps(data,ensure_ascii=False),{"event":"skill_loaded","sha256":digest(skill.encode()),"instructions_sha256":digest(system.encode())}

def validate(report,data):
    if not isinstance(report,dict) or set(report)!={"case_id","disposition","findings"}: raise ValueError("report keys")
    if len(json.dumps(report,ensure_ascii=False))>MAX_REPORT: raise ValueError("report character cap")
    if report["case_id"]!=data["case_id"]: raise ValueError("report ID mismatch")
    disp=report["disposition"]
    if disp not in {"findings","no_action","insufficient_context"}: raise ValueError("disposition")
    fs=report["findings"]
    if not isinstance(fs,list) or len(fs)>3: raise ValueError("findings cap")
    if (disp=="findings")!=bool(fs): raise ValueError("disposition/findings mismatch")
    for f in fs:
        if not isinstance(f,dict) or set(f)!={"category","path","line","quote","reason","verification"}: raise ValueError("finding keys")
        if f["category"] not in CATEGORIES: raise ValueError("category")
        if any(not isinstance(f[k],str) or not f[k].strip() for k in ["path","quote","reason","verification"]): raise ValueError("empty finding")
        text=data.get("files",{}).get(f["path"])
        if text is None: raise ValueError("path outside evidence")
        line=f["line"]
        if type(line)!=int or not 1<=line<=len(text.splitlines()): raise ValueError("line outside evidence")
        if f["quote"]!=text.splitlines()[line-1]: raise ValueError("quote mismatch")
    return report
