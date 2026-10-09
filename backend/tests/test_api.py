from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError

from backend.models import AppState, Conflict, Course, Obligation, Source
from backend.seed_data import seed_database


def writable(record):
    return {k: record[k] for k in ("course_id", "source_id", "title", "description", "obligation_type", "deadline", "status", "reference_url")}


def java_issue(client):
    return client.get('/conflicts?conflict_type=DEADLINE_CONFLICT').json()['items'][0]


def test_health_empty_database_and_frontend(client):
    assert client.get('/health').json()['status'] == 'ok'
    assert client.get('/dashboard').json()['total_obligations'] == 0
    assert client.get('/app/index.html').status_code == 200
    assert client.get('/docs').status_code == 200
    assert client.get('/openapi.json').status_code == 200
    assert client.post('/reconcile').json()['candidate_pairs'] == 0


def test_full_crud_and_relationships(client):
    course = client.post('/courses', json={'code':'cap205','name':'Next Gen Computing'})
    assert course.status_code == 201 and course.json()['code'] == 'CAP205'
    source = client.post('/sources',json={'name':'LMS','source_type':'LMS'})
    assert source.status_code == 201
    payload = {'source_id':source.json()['id'],'course_id':course.json()['id'], 'title':'  Assignment-02! ',
               'obligation_type':'Assignment','deadline':'2026-10-20','status':'Planned'}
    created = client.post('/obligations',json=payload)
    assert created.status_code == 201
    identifier = created.json()['id']
    assert created.json()['source']['name'] == 'LMS'
    assert created.json()['title'] == payload['title']
    assert client.delete('/sources/1').status_code == 409
    payload['deadline'] = '2026-10-22'
    assert client.put(f'/obligations/{identifier}',json=payload).json()['deadline'] == '2026-10-22'
    assert client.get(f'/obligations/{identifier}').json()['course']['code'] == 'CAP205'
    assert client.delete(f'/obligations/{identifier}').status_code == 204
    assert client.get(f'/obligations/{identifier}').status_code == 404
    assert client.delete('/sources/1').status_code == 204


def test_foreign_key_edit_refreshes_serialized_relationship(seeded):
    record=seeded.get('/obligations/1').json()
    data=writable(record); data.update(course_id=2,source_id=2)
    changed=seeded.put('/obligations/1',json=data).json()
    assert changed['course']['id']==2 and changed['source']['id']==2


def test_required_demo_and_repeat_dedup(seeded):
    first=seeded.post('/reconcile')
    assert first.status_code == 200
    assert first.json()['classifications'] == {'MATCH':1,'POTENTIAL_MATCH':2,'CONFLICT':1,'UNRELATED':2}
    issue=java_issue(seeded)
    assert issue['status']=='Needs Verification'
    assert {r['deadline'] for r in issue['source_records']}=={'2026-10-20','2026-10-22'}
    assert {r['source']['name'] for r in issue['source_records']}=={'LMS','Faculty Notice'}
    before=seeded.get('/conflicts').json()['total']
    assert seeded.post('/reconcile').json()['new_issues']==0
    assert seeded.get('/conflicts').json()['total']==before
    assert java_issue(seeded)['id']==issue['id']
    assert seeded.get('/obligations/1').json()['deadline']=='2026-10-20'


@pytest.mark.parametrize('status',['Needs Verification','Under Review','Resolved','Dismissed'])
def test_explicit_status_notes_survive_reconciliation(seeded,status):
    seeded.post('/reconcile'); issue=java_issue(seeded)
    response=seeded.put(f"/conflicts/{issue['id']}/status",json={'status':status,'resolution_notes':'Checked both synthetic sources.'})
    assert response.status_code==200
    seeded.post('/reconcile')
    current=java_issue(seeded)
    assert current['status']==status and current['resolution_notes']=='Checked both synthetic sources.'
    assert not current['evidence_changed']


def test_changed_reviewed_evidence_is_flagged_without_erasing_decision(seeded):
    seeded.post('/reconcile'); issue=java_issue(seeded)
    seeded.put(f"/conflicts/{issue['id']}/status",json={'status':'Resolved','resolution_notes':'Previous evidence checked.'})
    data=writable(seeded.get('/obligations/2').json()); data['deadline']='2026-10-23'
    seeded.put('/obligations/2',json=data)
    assert seeded.get('/reconciliation/results').json()['is_stale']
    seeded.post('/reconcile')
    updated=java_issue(seeded)
    assert updated['id']==issue['id'] and updated['status']=='Resolved' and updated['evidence_changed']
    results=seeded.get('/reconciliation/results?classification=CONFLICT').json()['items']
    assert results[0]['verification_status']=='Needs Verification'
    assert seeded.get('/dashboard').json()['unresolved_conflicts']==1


def test_fixed_issue_is_historical_never_automatically_resolved(seeded):
    seeded.post('/reconcile'); issue=java_issue(seeded)
    data=writable(seeded.get('/obligations/2').json()); data['deadline']='2026-10-20'
    seeded.put('/obligations/2',json=data); seeded.post('/reconcile')
    old=seeded.get(f"/conflicts/{issue['id']}").json()
    assert not old['is_current'] and old['status']=='Needs Verification'
    assert seeded.get('/conflicts?current_only=true&conflict_type=DEADLINE_CONFLICT').json()['total']==0


def test_deleted_records_keep_traceable_evidence(seeded,app):
    seeded.post('/reconcile'); issue=java_issue(seeded)
    assert seeded.delete('/obligations/1').status_code==204
    seeded.post('/reconcile')
    saved=seeded.get(f"/conflicts/{issue['id']}").json()
    assert len(saved['source_records'])==2 and saved['live_obligation_ids']==[2]
    assert saved['status']=='Needs Verification' and not saved['is_current']
    with app.state.session_factory() as db:
        assert db.execute(text('PRAGMA foreign_key_check')).all()==[]


def test_filter_search_sort_and_pagination(seeded):
    data=seeded.get('/obligations?q=Assignment%202&course_id=1&obligation_type=Assignment&sort_by=deadline&order=desc').json()
    assert data['total']==2 and data['items'][0]['deadline']=='2026-10-22'
    assert seeded.get('/obligations?missing_deadline=true').json()['total']==2
    assert seeded.get('/obligations?deadline_from=2026-10-21&deadline_to=2026-10-23').json()['total']==1
    assert len(seeded.get('/obligations?offset=1&limit=2').json()['items'])==2
    assert seeded.get('/obligations?q=%25').json()['total']==0  # '%' is literal, not a wildcard.
    seeded.post('/reconcile')
    result=seeded.get('/reconciliation/results?classification=CONFLICT&course_id=1&issue_type=DEADLINE_CONFLICT').json()
    assert result['total']==1
    assert seeded.get('/conflicts?conflict_type=MISSING_DEADLINE').json()['total']==2


@pytest.mark.parametrize('path,payload',[
    ('/courses',{'code':' ','name':'Java'}),
    ('/sources',{'name':'','source_type':'LMS'}),
    ('/sources',{'name':'x','source_type':'Unknown'}),
    ('/sources',{'name':'x','source_type':'LMS','reference_url':'javascript:alert(1)'}),
    ('/sources',{'name':'x','source_type':'LMS','last_checked_at':'2999-01-01T00:00:00Z'}),
    ('/obligations',{'source_id':999,'title':'Invalid reference'}),
    ('/obligations',{'source_id':1,'course_id':999}),
    ('/obligations',{'source_id':1,'deadline':'2026-02-30'}),
    ('/obligations',{'source_id':1,'status':'Invented'}),
    ('/obligations',{'source_id':1,'title':'a'*241}),
    ('/obligations',{'source_id':1,'unexpected':True}),
])
def test_validation_errors(seeded,path,payload):
    assert seeded.post(path,json=payload).status_code==422


def test_error_codes_and_incomplete_records(seeded):
    assert seeded.get('/obligations/999').status_code==404
    assert seeded.get('/sources/999').status_code==404
    assert seeded.get('/conflicts/999').status_code==404
    assert seeded.put('/conflicts/999/status',json={'status':'Resolved'}).status_code==404
    assert seeded.post('/courses',json={'code':'CAP205','name':'duplicate'}).status_code==409
    assert seeded.post('/sources',json={'name':'LMS','source_type':'LMS'}).status_code==409
    assert seeded.get('/obligations?sort_by=arbitrary').status_code==422
    assert seeded.get('/obligations?limit=9999').status_code==422
    assert seeded.get('/obligations?deadline_from=2026-10-22&deadline_to=2026-10-20').status_code==422
    assert seeded.post('/obligations',json={'source_id':1}).status_code==201
    seeded.post('/reconcile')
    assert seeded.get('/conflicts?conflict_type=INCOMPLETE_INFORMATION').json()['total']>=2


def test_database_enforces_real_foreign_keys(seeded,app):
    with app.state.session_factory() as db:
        assert db.execute(text('PRAGMA foreign_keys')).scalar()==1
        db.add(Obligation(source_id=999,title='Broken FK'))
        with pytest.raises(IntegrityError): db.commit()
        db.rollback()
        with pytest.raises(IntegrityError):
            db.execute(delete(Source).where(Source.id==1)); db.commit()
        db.rollback()
        assert db.get(Obligation,1).source.name=='LMS'
        assert db.get(Course,1).obligations


def test_seed_is_non_destructive_and_idempotent(seeded,app):
    with app.state.session_factory() as db:
        assert not seed_database(db)['seeded']
    assert seeded.get('/dashboard').json()['total_obligations']==12


def test_seed_refuses_to_mix_with_existing_user_data(client,app):
    client.post('/sources',json={'name':'My real source','source_type':'Manual'})
    with app.state.session_factory() as db:
        with pytest.raises(ValueError): seed_database(db)


def test_concurrent_reconciliation_serializes_without_duplicate_issues(seeded):
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _: seeded.post('/reconcile'),range(2)))
    assert [r.status_code for r in responses]==[200,200]
    assert sorted(r.json()['new_issues'] for r in responses)==[0,9]
    assert seeded.get('/conflicts').json()['total']==9


def test_empty_run_marks_old_issues_historical(seeded):
    seeded.post('/reconcile')
    for record in seeded.get('/obligations').json()['items']:
        assert seeded.delete('/obligations/'+str(record['id'])).status_code==204
    assert seeded.post('/reconcile').json()['candidate_pairs']==0
    assert seeded.get('/conflicts?current_only=true').json()['total']==0
    assert seeded.get('/conflicts').json()['total']==9


def test_deleted_source_ids_are_not_reused(client):
    first=client.post('/sources',json={'name':'Temporary','source_type':'Manual'}).json()
    assert client.delete('/sources/'+str(first['id'])).status_code==204
    second=client.post('/sources',json={'name':'Replacement','source_type':'Manual'}).json()
    assert second['id'] > first['id']


def test_dashboard_counts_punctuation_only_title_as_incomplete(seeded):
    before=seeded.get('/dashboard').json()['incomplete_records']
    payload=writable(seeded.get('/obligations/1').json());payload['title']='!!!'
    seeded.post('/obligations',json=payload)
    assert seeded.get('/dashboard').json()['incomplete_records']==before+1


def test_cli_initialization_and_seed(tmp_path):
    import os
    import subprocess
    import sys
    env={**os.environ,'DATABASE_URL':f"sqlite:///{tmp_path / 'cli.db'}"}
    for module in ['backend.init_db','backend.seed_data','backend.database','backend.seed_data']:
        result=subprocess.run([sys.executable,'-m',module],env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    assert 'already loaded' in result.stdout
