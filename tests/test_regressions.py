import importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
r=Path(__file__).resolve().parents[1];p=r/'scripts'
spec=importlib.util.spec_from_file_location('fixed',p/'job_search.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=r
m.self_test()
cfg={'candidate':{'skills':['Java','Go']},'preferences':{'minimum_score':2}}
assert m.assess(m.normalized_job('test','1','X','Java Developer','https://example.com/1','2026-09-24','Worldwide','Build services'),cfg)
assert m.assess(m.normalized_job('test','1','X','Frontend Java Developer','https://example.com/1','2026-09-24','Worldwide','Build services'),cfg) is None
src={'kind':'remoteok','name':'Remote OK','url':'https://remoteok.com/api','feeds':['https://remoteok.com/remote-java-jobs.json'],'query_delay_seconds':0}
row={'id':'1','position':'Java Developer','description':None,'location':'','tags':[]}
with patch.object(m,'fetch_json',side_effect=[[{'legal':'terms'},row],[row,dict(row,id='2')]]):
 jobs=m.fetch_source(src);assert len(jobs)==2 and jobs[0]['remote_scope_raw']=='Not stated';assert m.assess(jobs[0],cfg)['china_feasibility']!='可直接投'
with patch.object(m,'fetch_json',side_effect=[RuntimeError(),[row]]):
 assert len(m.fetch_source(src))==1 and src['fetch_diagnostics']['errors']
print('REGRESSION OK: category dedup, missing location, null description, partial failure, Java recognition')

assert m.load_company_exclusions(r) == {}
for location in ['United States (Remote)', 'Remote, Canada', 'Remote, Canada; Remote, United States', 'Germany (Remote)', 'Remote, Poland', 'Remote-EMEA']:
    job=m.normalized_job('test','1','Example','Backend Engineer','https://example.com/jobs/1','2026-09-24',location,'Build backend APIs')
    assert m.assess(job,cfg)['china_feasibility']=='不建议投', location
for location in ['Remote','Worldwide','China','Remote, APAC','Remote, Asia','Remote, Global']:
    job=m.normalized_job('test','1','Example','Backend Engineer','https://example.com/jobs/1','2026-09-24',location,'Build backend APIs')
    assert m.assess(job,cfg)['china_feasibility']!='不建议投', location
print('LOCATION AND OPTIONAL CONFIG REGRESSIONS OK')

language_cfg={'candidate':{'skills':['Redis','AWS','Java']},'preferences':{'minimum_score':2,'required_languages':['Go','Java','Python','Kotlin']}}
def language_job(description):
    return m.assess(m.normalized_job('test','language','Example','Backend Engineer','https://example.com/language','2026-09-24','Worldwide',description), language_cfg)
for description in ['Java Spring services', 'Python APIs', 'Kotlin services', 'Go backend services', 'Golang backend services']:
    assert language_job(description) is not None, description
for description in ['JavaScript Node.js', 'Rust with Redis and Kafka', 'go to market', 'distributed systems with PostgreSQL']:
    assert language_job(description) is None, description
assert language_job('Java Redis AWS Kafka')['score'] == language_job('Java')['score']
assert language_job('Golang. Location: Mostly remote (within Germany), with monthly in-person collaboration at our Berlin office')['china_feasibility'] == '不建议投'
print('LANGUAGE AND PARENTHESIZED LOCATION REGRESSIONS OK')
