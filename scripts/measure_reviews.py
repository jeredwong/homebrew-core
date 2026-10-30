"""Reproduce a descriptive review-latency proxy from saved GitHub API records."""
import datetime,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def measure(sample):
    rows=[]
    def stamp(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
    for pr in sample['rows']:
        reviews=[r for r in pr['reviews'] if r['submitted_at'] and r['type']=='User' and r['login'] not in {pr['author'],'BrewTestBot'} and r['state']!='PENDING']
        first=min(reviews,key=lambda r:r['submitted_at']) if reviews else None
        hours=(stamp(first['submitted_at'])-stamp(pr['created_at'])).total_seconds()/3600 if first else None
        if hours is not None and hours<0:raise ValueError('review predates PR')
        rows.append({'number':pr['number'],'first_review_id':first['id'] if first else None,'hours':hours})
    values=sorted(r['hours'] for r in rows if r['hours'] is not None)
    return {'sample_size':len(rows),'observed_reviews':len(values),'without_qualifying_review':len(rows)-len(values),'median_hours_observed':statistics.median(values) if values else None,'p75_hours_observed_nearest_rank':values[math.ceil(.75*len(values))-1] if values else None,'over_24_hours_observed':sum(v>24 for v in values),'definition':'First submitted review by a non-author GitHub User other than BrewTestBot. User accounts can still be automated; issue comments are excluded. Missing reviews are not assigned zero latency.','sampling':sample['sampling'],'rows':rows}
if __name__=='__main__':
    result=measure(json.loads((ROOT/'evidence/pr-review-sample.json').read_text()))
    (ROOT/'evidence/pr-review-latency.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
