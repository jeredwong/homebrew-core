"""Trusted manual PR intake, restricted to the Actions sandbox repository."""
import base64,json,os,re,subprocess,urllib.request
from pathlib import Path
from prepare_input import prepare,SHA
from reviewer import MAX_INPUT

def main():
    repo=os.environ['GITHUB_REPOSITORY'];number=os.environ['PR_NUMBER']
    if repo=='Homebrew/homebrew-core' or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):raise ValueError('sandbox repository required')
    if not re.fullmatch(r'[1-9][0-9]{0,8}',number):raise ValueError('numeric PR required')
    url=f'https://api.github.com/repos/{repo}/pulls/{number}'
    request=urllib.request.Request(url,headers={'Authorization':'Bearer '+os.environ['GH_READ_TOKEN'],'Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(request,timeout=30) as response:
        raw=response.read(1000001)
    if len(raw)>1000000:raise ValueError('PR metadata cap')
    pr=json.loads(raw);base=pr['base']['sha'];head=pr['head']['sha']
    if not SHA.fullmatch(base) or not SHA.fullmatch(head):raise ValueError('invalid API commit SHA')
    # Fetch fixed ref/SHAs from this repository, never a URL supplied by the PR.
    # Token is scoped to this trusted Git process, not persisted in .git/config.
    git_env=dict(os.environ)
    auth=base64.b64encode(('x-access-token:'+os.environ['GH_READ_TOKEN']).encode()).decode()
    git_env.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',GIT_CONFIG_VALUE_0='AUTHORIZATION: basic '+auth)
    subprocess.run(['git','fetch','--no-tags','--depth=2','https://github.com/'+repo+'.git',base,f'refs/pull/{number}/head'],check=True,timeout=60,env=git_env)
    d=prepare('.',base,head,'pr-'+number)
    d['untrusted_pr']={'title':pr.get('title',''),'body':pr.get('body') or ''}
    if len(json.dumps(d).encode())>MAX_INPUT:raise ValueError('combined input cap')
    p=Path('work/prepared.json');p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
if __name__=='__main__':main()
