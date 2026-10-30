import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reviewer import ROOT,load_case,load_prepared,validate
from prepare_input import prepare
from prepare_replay import prepare as export
from import_replay import ingest
from adjudicate import template
from evaluate import evaluate
from measure_reviews import measure
import run_claude_code,prepare_pr

class Revision(unittest.TestCase):
 def test_semantic_gate_does_not_accept_plausible_category_and_quote(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp)/'wslay-before';folder.mkdir();actual=folder/'actual.json'
   r=json.loads((ROOT/'evals/golden/wslay-before/actual.json').read_text())
   r['findings'][0]['reason']='The moon is made of cheese.'
   actual.write_text(json.dumps(r));validate(r,load_case('wslay-before'))
   result=evaluate(tmp)['cases'][0]
   self.assertTrue(result['category_agreement']);self.assertEqual(result['semantic_status'],'pending')
   a=template('wslay-before',actual);a['reviewer']='test fixture reviewer'
   for c in a['criteria']:c.update(passed=True,reason='Test fixture only')
   (folder/'adjudication.json').write_text(json.dumps(a))
   self.assertEqual(evaluate(tmp)['cases'][0]['semantic_status'],'accepted')
   # Repeated criteria cannot substitute for reviewing each rubric criterion.
   a['criteria']=[a['criteria'][0]]*len(a['criteria']);(folder/'adjudication.json').write_text(json.dumps(a))
   self.assertEqual(evaluate(tmp)['cases'][0]['semantic_status'],'pending')
 def test_adjudication_invalidated_by_changed_report(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp)/'wslay-before';folder.mkdir();actual=folder/'actual.json'
   actual.write_bytes((ROOT/'evals/golden/wslay-before/actual.json').read_bytes())
   a=template('wslay-before',actual);a['reviewer']='test fixture reviewer'
   for c in a['criteria']:c.update(passed=True,reason='Test fixture only')
   (folder/'adjudication.json').write_text(json.dumps(a));actual.write_text(actual.read_text()+'\n')
   self.assertEqual(evaluate(tmp)['cases'][0]['semantic_status'],'pending')
 def test_replay_export_and_import_preserve_real_record(self):
  with tempfile.TemporaryDirectory() as tmp:
   bundle=Path(tmp)/'bundle';export('wslay-before',bundle)
   self.assertEqual({x.name for x in bundle.iterdir()},{'instructions.txt','input.json','bundle.json'})
   self.assertEqual(json.loads((bundle/'input.json').read_text())['case_id'],'review')
   record=ROOT/'evals/golden/wslay-before/assistant-record.json';out=Path(tmp)/'import'
   ingest('wslay-before',bundle,record,out)
   self.assertEqual((out/'wslay-before/assistant-record.json').read_bytes(),record.read_bytes())
   self.assertEqual(json.loads((out/'wslay-before/actual.json').read_text())['case_id'],'wslay-before')
   (bundle/'input.json').write_text('{}')
   self.assertRaises(ValueError,ingest,'wslay-before',bundle,record,Path(tmp)/'bad')
 def test_prepared_input_rejects_traversal(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'input.json';d=load_case('wslay-before');d['case_id']='../../outside';p.write_text(json.dumps(d))
   self.assertRaises(ValueError,load_prepared,p)
 def test_git_intake_reviews_only_formula_changes(self):
  with tempfile.TemporaryDirectory() as tmp:
   def git(*args):return subprocess.check_output(['git','-C',tmp,*args],text=True,stderr=subprocess.DEVNULL).strip()
   git('init');git('config','user.name','Test');git('config','user.email','test@example.invalid')
   p=Path(tmp)/'Formula/a/a.rb';p.parent.mkdir(parents=True);p.write_text('class A < Formula\nend\n');git('add','.');git('commit','-m','base');base=git('rev-parse','HEAD')
   p.write_text('class A < Formula\n  test do\n  end\nend\n');git('add','.');git('commit','-m','head');head=git('rev-parse','HEAD')
   self.assertIn('Formula/a/a.rb',prepare(tmp,base,head,'pr-1')['files'])
   self.assertRaises(ValueError,prepare,tmp,'--help',head,'pr-1')
   (Path(tmp)/'workflow.yml').write_text('untrusted');git('add','.');git('commit','-m','non-formula')
   self.assertRaises(ValueError,prepare,tmp,base,git('rev-parse','HEAD'),'pr-1')
 def test_cli_missing_credentials_never_starts_process(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{},clear=True),patch('run_claude_code.shutil.which',return_value=None),patch('run_claude_code.subprocess.run') as run:
   self.assertRaises(RuntimeError,run_claude_code.run,'wslay-before',tmp);run.assert_not_called()
   self.assertIn('"inference_attempted": false',(Path(tmp)/'wslay-before/transcript.jsonl').read_text())
 def test_cli_wiring_uses_skill_no_tools_and_no_github_credentials(self):
  report=(ROOT/'evals/golden/wslay-before/actual.json').read_text()
  with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'ANTHROPIC_API_KEY':'stub','GH_READ_TOKEN':'must-not-pass'}),patch('run_claude_code.shutil.which',return_value='/stub/claude'),patch('run_claude_code.subprocess.check_output',return_value=run_claude_code.CLI_VERSION+' (Claude Code)'),patch('run_claude_code.subprocess.run') as run:
   def response(args,**kw):
    self.assertEqual(args[args.index('--tools')+1],'');self.assertEqual(args[args.index('--disallowedTools')+1],'*')
    self.assertNotIn('GH_READ_TOKEN',kw['env']);self.assertEqual(kw['timeout'],90)
    instructions=Path(args[args.index('--system-prompt-file')+1]).read_text();self.assertIn('Formula review procedure',instructions)
    self.assertEqual(json.loads(kw['input'])['case_id'],'wslay-before')
    return subprocess.CompletedProcess(args,0,json.dumps({'is_error':False,'result':report,'total_cost_usd':0.01}),'')
   run.side_effect=response;run_claude_code.run('wslay-before',tmp)
   self.assertTrue((Path(tmp)/'wslay-before/runtime-output.json').exists())
 def test_pr_intake_rejects_upstream_and_invalid_numbers_before_network(self):
  for repo,number in [('Homebrew/homebrew-core','1'),('owner/sandbox','--upload')]:
   with patch.dict(os.environ,{'GITHUB_REPOSITORY':repo,'PR_NUMBER':number}),patch('prepare_pr.urllib.request.urlopen') as request:
    self.assertRaises(ValueError,prepare_pr.main);request.assert_not_called()
 def test_pr_intake_ignores_untrusted_clone_url(self):
  class Response:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,n):return json.dumps({'base':{'sha':'a'*40},'head':{'sha':'b'*40,'repo':{'clone_url':'https://attacker.invalid/'}},'title':'Example','body':'untrusted'}).encode()
  with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'GITHUB_REPOSITORY':'owner/sandbox','PR_NUMBER':'42','GH_READ_TOKEN':'stub'}),patch('prepare_pr.urllib.request.urlopen',return_value=Response()),patch('prepare_pr.subprocess.run') as fetch,patch('prepare_pr.prepare',return_value={'case_id':'pr-42','files':{}}):
   prior=os.getcwd()
   try:
    os.chdir(tmp);prepare_pr.main()
   finally:os.chdir(prior)
   args=fetch.call_args.args[0];self.assertIn('https://github.com/owner/sandbox.git',args)
   self.assertNotIn('https://attacker.invalid/',args);self.assertNotIn('stub',' '.join(args))
   self.assertEqual(json.loads((Path(tmp)/'work/prepared.json').read_text())['untrusted_pr']['body'],'untrusted')
 def test_review_metric_excludes_author_and_bot_and_keeps_missing(self):
  def review(login,kind,time):return {'id':time,'submitted_at':'2026-09-01T0'+str(time)+':00:00Z','login':login,'type':kind,'state':'APPROVED'}
  pr={'number':1,'author':'author','created_at':'2026-09-01T00:00:00Z','reviews':[review('author','User',1),review('bot','Bot',2),review('person','User',3)]}
  result=measure({'sampling':'test','rows':[pr,dict(pr,number=2,reviews=[])]})
  self.assertEqual(result['median_hours_observed'],3);self.assertEqual(result['without_qualifying_review'],1)
if __name__=='__main__':unittest.main()
