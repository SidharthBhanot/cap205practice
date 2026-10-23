import { api, params } from './api.js';
import { $, mount, icon, badge, label, date, time, escapeHTML as e, options, issueTypes, reviewStatuses, errorState, empty, modal, toast, staleNotice, run, recordDetail, pagination } from './common.js';

mount('conflicts','Conflicts & verification','Review source evidence, record your decision, and preserve the explanation.',
  `<button class="btn" id="run">${icon('reconcile')}Run reconciliation</button>`);
let offset=0, sequence=0;
const limit=12;
function evidence(issue) {
  return `<div class="issue-evidence-grid">${issue.source_records.map(record=>`<div class="issue-evidence"><span class="small-text muted">${e(record.source.name)} · Record #${record.id}</span><strong class="${!record.deadline ? 'deadline-missing' : issue.conflict_type==='DEADLINE_CONFLICT' ? 'deadline-conflict' : ''}">${record.deadline ? date(record.deadline) : 'Deadline not recorded'}</strong><span class="small-text">${e(record.title || 'Untitled record')}</span></div>`).join('')}</div>`;
}
function issueCard(issue) {
  const course=issue.source_records[0]?.course;
  return `<article class="verification-card"><header class="verification-card-header"><div class="badge-row">${badge(issue.conflict_type)}${badge(issue.status)}</div><span class="small-text muted">#${issue.id}${!issue.is_current?' · Historical':''}</span></header><h2>${e(course ? course.code+' · '+course.name : 'Course not recorded')}</h2>${evidence(issue)}<p class="issue-reason">${e(issue.explanation)}</p>${issue.evidence_changed?'<div class="notice amber">Evidence changed after review. Verify again.</div>':''}<footer class="verification-card-footer"><span class="small-text muted">Last detected ${date(issue.last_detected_at)}${issue.resolution_notes?' · Review notes saved':''}</span><button class="btn secondary" data-review="${issue.id}">Review evidence</button></footer></article>`;
}
async function init() {
  try {
    const courses=await api('/courses');
    $('#content').innerHTML=`<div id="freshness"></div><form class="toolbar" id="filters"><label>Verification status<select name="status">${options(reviewStatuses)}</select></label><label>Issue type<select name="conflict_type">${options(issueTypes)}</select></label><label>Course<select name="course_id">${options(courses.map(c=>({id:c.id,name:c.code+' · '+c.name})))}</select></label><label>Detection scope<select name="current_only"><option value="true">Latest run only</option><option value="false">Include historical issues</option></select></label></form><div class="filter-foot"><span id="issue-count"></span><span>Only you can resolve or dismiss an issue.</span></div><section aria-label="Verification issues"><div id="issues" class="verification-list"><div class="loading">Loading verification queue…</div></div><div class="pagination" id="pagination"></div></section>`;
    $('#filters').onsubmit=event=>event.preventDefault();$('#filters').onchange=()=>{offset=0;load();};
    await load();
    const id=new URLSearchParams(location.search).get('id');if(id)await detail(Number(id));
  }catch(error){errorState(error);}
}
async function load() {
  const request=++sequence;
  try {
    const [d,dashboard]=await Promise.all([api('/conflicts'+params({...Object.fromEntries(new FormData($('#filters'))),offset,limit})),api('/dashboard')]);
    if(request!==sequence)return;
    if(offset>=d.total && offset>0){offset=0;return load();}
    $('#freshness').innerHTML=staleNotice(dashboard.is_stale,dashboard.last_reconciled_at);
    $('#issue-count').textContent=`${d.total} issue${d.total===1?'':'s'}`;
    $('#issues').innerHTML=d.items.length ? d.items.map(issueCard).join('') : empty('No issues in this view','Run reconciliation or adjust your filters. Historical issues remain available until you explicitly review them.');
    pagination(d.total,offset,limit,next=>{offset=next;load();});
    document.querySelectorAll('[data-review]').forEach(b=>b.onclick=()=>detail(Number(b.dataset.review)).catch(error=>toast(error.message,true)));
  }catch(error){if(request===sequence)errorState(error,'#issues',load);}
}
async function detail(id) {
  const issue=await api('/conflicts/'+id);
  const liveIDs=issue.live_obligation_ids;
  modal({title:`Issue #${issue.id} · ${label(issue.conflict_type)}`,wide:true,submitText:'Save review decision',body:`<div class="badge-row">${badge(issue.status)}${badge(issue.conflict_type)}${!issue.is_current?'<span class="badge neutral">Not detected in the latest run</span>':''}</div><p style="margin-top:16px">${e(issue.explanation)}</p><div class="notice amber"><div><strong>Verify the original sources before deciding.</strong> This system does not choose a correct source, change a deadline, or merge records.</div></div>${issue.evidence_changed?'<div class="notice amber"><div><strong>Evidence changed after the last review.</strong> Your previous status and notes are preserved. Verify this new evidence before relying on that decision.</div></div>':''}<h3>Reported deadlines</h3>${evidence(issue)}<details class="rule-box"><summary>Full evidence from the latest detection</summary><div class="detail-grid">${issue.source_records.map(r=>recordDetail(r,liveIDs.includes(r.id))).join('')}</div></details><details class="rule-box"><summary>View current live records (${issue.current_records.length})</summary><p>These may differ from the detection snapshot if a record was edited. Run reconciliation to refresh evidence.</p><div class="detail-grid">${issue.current_records.map(r=>recordDetail(r)).join('') || '<p>The original records have been deleted. Their detection snapshots remain above.</p>'}</div></details><p class="small-text muted">First detected ${time(issue.detected_at)} · Last detected ${time(issue.last_detected_at)}${issue.reviewed_at?' · Last reviewed '+time(issue.reviewed_at):''}</p><h3>Your review decision</h3><div class="review-form form-grid"><label>Verification status<select name="status">${options(reviewStatuses,issue.status,null)}</select></label><div class="form-help">A decision changes this issue only. To correct a record, edit it separately and run reconciliation again.</div><label class="full">Resolution notes<textarea name="resolution_notes" maxlength="10000" placeholder="What did you check, and why did you make this decision?">${e(issue.resolution_notes)}</textarea></label></div>`,onSubmit:async data=>{
    await api('/conflicts/'+id+'/status',{method:'PUT',body:Object.fromEntries(data)});toast('Review saved. Original source records are unchanged.');await load();
  }});
}
$('#run').onclick=event=>run(event.currentTarget,load);
init();
