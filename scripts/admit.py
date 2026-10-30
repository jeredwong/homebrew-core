"""Conservative quota guard: count all workflow launches, including failed admissions.
Single concurrency group serializes admission; interrupted/pending jobs may be lost.
No model receives this job's read-only GitHub token.
"""
import datetime,json,os,urllib.request

def weight(run): return (18 if run["event"]=="schedule" else 1)*int(run.get("run_attempt",1))
def permitted(runs,now):
    day=now.date();week=now.date()-datetime.timedelta(days=now.weekday())
    daily=weekly=0
    for r in runs:
        d=datetime.datetime.fromisoformat(max(r["created_at"],r.get("updated_at",r["created_at"])).replace("Z","+00:00")).date()
        if d>=week: weekly+=weight(r)
        if d==day: daily+=weight(r)
    return daily<=20 and weekly<=100

def main():
    now=datetime.datetime.now(datetime.timezone.utc);since=(now-datetime.timedelta(days=8)).date().isoformat()
    repo=os.environ["GITHUB_REPOSITORY"];token=os.environ["GH_READ_TOKEN"]
    runs=[]
    for page in range(1,12):
        url=f"https://api.github.com/repos/{repo}/actions/workflows/formula-review.yml/runs?per_page=100&page={page}&created=%3E%3D{since}"
        req=urllib.request.Request(url,headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json"})
        with urllib.request.urlopen(req,timeout=30) as f: obj=json.load(f)
        if obj["total_count"]>1000: raise RuntimeError("quota history exceeds retrievable window; fail closed")
        runs.extend(obj["workflow_runs"])
        if len(runs)>=obj["total_count"]: break
    if not any(str(r["id"])==os.environ["GITHUB_RUN_ID"] for r in runs): raise RuntimeError("current run not visible; fail closed")
    if not permitted(runs,now): raise RuntimeError("quota exhausted")
    print(json.dumps({"admitted":True,"runs_considered":len(runs),"limits":{"daily":20,"weekly":100},"accounting":"conservative, failed launches count"}))
if __name__=="__main__": main()
