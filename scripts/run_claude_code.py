"""Configure the existing Claude Code agent as a tool-free formula reviewer.
CLI flags: https://code.claude.com/docs/en/cli-reference
"""
import argparse,json,os,shutil,subprocess,tempfile,time
from pathlib import Path
from reviewer import MODEL,load_case,load_prepared,build_prompt,validate
CLI_VERSION='2.1.290'

def command(executable,system_file):
    return [executable,'--bare','--restricted','--print','--tools','','--disallowedTools','*','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence','--disable-slash-commands','--system-prompt-file',str(system_file),'--model',MODEL,'--max-turns','1','--max-budget-usd','0.50','--output-format','json']

def run(case,out,input_path=None):
    data=load_prepared(input_path) if input_path else load_case(case)
    system,user,loaded=build_prompt(data);target=Path(out)/data['case_id'];target.mkdir(parents=True,exist_ok=False)
    events=[{'event':'start','engine':'Claude Code','requested_version':CLI_VERSION,'model':MODEL,'time':time.time()},loaded,{'role':'system','content':system},{'role':'user','content':user}]
    def log():(target/'transcript.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    log()
    executable=shutil.which('claude')
    if not executable or not os.environ.get('ANTHROPIC_API_KEY'):
        events.append({'event':'blocked','reason':'Claude Code executable or ANTHROPIC_API_KEY missing','inference_attempted':False});log();raise RuntimeError('Claude Code executable and ANTHROPIC_API_KEY required')
    try:
        version=subprocess.check_output([executable,'--version'],text=True,timeout=10).strip()
        if version.split()[0]!=CLI_VERSION:raise ValueError('unreviewed CLI version')
        with tempfile.TemporaryDirectory(prefix='formula-review-') as temp:
            p=Path(temp);(p/'instructions.txt').write_text(system)
            # No GitHub token, user hooks, repository config, or credential discovery.
            keep=['PATH','HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy','SSL_CERT_FILE','NODE_EXTRA_CA_CERTS','ANTHROPIC_API_KEY']
            env={k:os.environ[k] for k in keep if k in os.environ};env.update(CLAUDE_CONFIG_DIR=str(p/'config'),CLAUDE_CODE_MAX_OUTPUT_TOKENS='2200',DISABLE_AUTOUPDATER='1')
            result=subprocess.run(command(executable,p/'instructions.txt'),input=user,text=True,capture_output=True,cwd=p,env=env,timeout=90)
        if len(result.stdout)>1000000:raise ValueError('CLI output cap')
        # Preserve actual runtime output, not a reconstructed model response.
        (target/'runtime-output.json').write_text(result.stdout)
        if result.returncode:raise RuntimeError('Claude Code returned failure; inspect runtime output')
        response=json.loads(result.stdout)
        if response.get('is_error'):raise ValueError('agent execution error')
        report=validate(json.loads(response['result']),data)
        (target/'actual.json').write_text(json.dumps(report,indent=2)+'\n')
        events.append({'event':'validated','runtime':response,'cli_version':version})
    except Exception as exc:
        events.append({'event':'failed','exception_type':type(exc).__name__});raise
    finally:log()
if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--case');g.add_argument('--input');p.add_argument('--out',required=True);a=p.parse_args();run(a.case,a.out,a.input)
