import copy,datetime,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reviewer import ROOT,load_case,build_prompt,validate
from admit import permitted
import run_agent
class Controls(unittest.TestCase):
 def setUp(self):
  self.data=load_case('wslay-before');self.report=json.loads((ROOT/'evals/golden/wslay-before/actual.json').read_text())
 def test_quotes_are_checked(self):
  self.report['findings'][0]['quote']='invented';self.assertRaises(ValueError,validate,self.report,self.data)
 def test_paths_and_traversal(self):
  self.assertRaises(ValueError,load_case,'../../expected')
  self.report['findings'][0]['path']='../../.env';self.assertRaises(ValueError,validate,self.report,self.data)
 def test_output_cap(self):
  self.report['findings']*=4;self.assertRaises(ValueError,validate,self.report,self.data)
 def test_arbitrary_actions_rejected(self):
  self.report['close_issues']=[1,2];self.assertRaises(ValueError,validate,self.report,self.data)
 def test_bad_disposition(self):
  self.report['disposition']='no_action';self.assertRaises(ValueError,validate,self.report,self.data)
 def test_skill_explicitly_loaded_not_expected(self):
  system,user,event=build_prompt(self.data)
  self.assertIn('Formula review procedure',system);self.assertEqual(event['event'],'skill_loaded');self.assertNotIn('later_selection_reference',user)
 def test_prompt_injections_have_no_tools(self):
  for case in ['attack-issue','attack-tool']:
   d=load_case(case);self.assertTrue(d['files']);self.assertIn('untrusted_',json.dumps(d))
  source=(ROOT/'scripts/run_agent.py').read_text();self.assertNotIn('eval(',source);self.assertNotIn('subprocess',source)
 def test_300_attempts_conservative_cap(self):
  now=datetime.datetime(2026,10,26,tzinfo=datetime.timezone.utc);runs=[];admitted=0
  for n in range(300):
   # Spread across all 7 days, respecting 20/day. Failed admissions still count.
   d=now+datetime.timedelta(days=n%7);runs.append({'event':'workflow_dispatch','created_at':d.isoformat()})
  # Chronological replay of 300 requests, 43/day for first six days.
  runs=[]
  for day in range(7):
   current=now+datetime.timedelta(days=day)
   for n in range(43 if day<6 else 42):
    runs.append({'event':'workflow_dispatch','created_at':current.isoformat()});admitted+=permitted(runs,current)
  self.assertEqual(admitted,54) # 20 + 20 + 14; rejected launches also consume budget
  self.assertLessEqual(admitted,100)
 def test_schedule_reserves_18(self):
  now=datetime.datetime(2026,10,26,tzinfo=datetime.timezone.utc)
  r=[{'event':'schedule','created_at':now.isoformat()}]+[{'event':'workflow_dispatch','created_at':now.isoformat()}]*2
  self.assertTrue(permitted(r,now));self.assertFalse(permitted(r+[r[-1]],now))
 def test_retry_counts(self):
  now=datetime.datetime(2026,10,26,tzinfo=datetime.timezone.utc)
  self.assertFalse(permitted([{'event':'workflow_dispatch','created_at':now.isoformat(),'run_attempt':21}],now))
 def test_missing_key_fails_without_network(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict('os.environ',{},clear=True),patch('urllib.request.build_opener') as call:
   self.assertRaises(RuntimeError,run_agent.run,'wslay-before',tmp);call.assert_not_called()
   log=(Path(tmp)/'wslay-before/transcript.jsonl').read_text();self.assertIn('skill_loaded',log)
 def test_real_api_payload_and_validation_using_transport_stub(self):
  class Response:
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self,n):return json.dumps({'content':[{'type':'text','text':json.dumps(self_report)}],'stop_reason':'end_turn','usage':{'input_tokens':10,'output_tokens':10}}).encode()
  self_report=self.report
  with tempfile.TemporaryDirectory() as tmp,patch.dict('os.environ',{'ANTHROPIC_API_KEY':'test-only'}),patch('urllib.request.build_opener') as opener:
   opener.return_value.open.return_value=Response();run_agent.run('wslay-before',tmp)
   req=opener.return_value.open.call_args.args[0];body=json.loads(req.data)
   self.assertNotIn('tools',body);self.assertEqual(req.full_url,'https://api.anthropic.com/v1/messages');self.assertIn('Formula review procedure',body['system'])
   self.assertTrue((Path(tmp)/'wslay-before/actual.json').exists())
if __name__=='__main__':unittest.main()
