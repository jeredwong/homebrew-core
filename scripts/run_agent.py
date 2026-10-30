"""Claude API platform equivalent. No model tools, execution, or GitHub API access."""
import argparse,json,os,time,urllib.request
from pathlib import Path
from reviewer import MODEL,load_case,build_prompt,validate,digest,load_prepared

def run(case_id,out,input_path=None):
    data=load_prepared(input_path) if input_path else load_case(case_id)
    case_id=data["case_id"]
    system,user,loaded=build_prompt(data)
    out=Path(out)/case_id;out.mkdir(parents=True,exist_ok=False)
    events=[{"event":"start","case_id":case_id,"model":MODEL,"input_sha256":digest(user.encode()),"time":time.time()},loaded]
    def log(): (out/"transcript.jsonl").write_text("".join(json.dumps(e)+"\n" for e in events))
    log()
    key=os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        events.append({"event":"blocked","reason":"missing provider credential","inference_attempted":False});log()
        raise RuntimeError("ANTHROPIC_API_KEY is not configured; no inference attempted")
    payload={"model":MODEL,"max_tokens":2200,"temperature":0,"system":system,"messages":[{"role":"user","content":user}]}
    # Destination is a constant. No redirects: credential cannot follow a 30x.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs): return None
    req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=json.dumps(payload).encode(),headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=90) as response:
            raw=response.read(1000001)
        if len(raw)>1000000: raise ValueError("provider response cap")
        obj=json.loads(raw)
        events.append({"event":"provider_response","response":obj})
        text="".join(b["text"] for b in obj["content"] if b.get("type")=="text")
        if obj.get("stop_reason")!="end_turn": raise ValueError("incomplete response")
        report=validate(json.loads(text),data)
        (out/"actual.json").write_text(json.dumps(report,indent=2)+"\n")
        events.append({"event":"validated","usage":obj.get("usage"),"cost":"not returned by API"})
    except Exception as exc:
        # Avoid exception strings potentially containing authentication headers.
        events.append({"event":"failed","exception_type":type(exc).__name__})
        raise
    finally: log()
if __name__=="__main__":
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--case');g.add_argument('--input');p.add_argument('--out',required=True);a=p.parse_args();run(a.case,a.out,a.input)
