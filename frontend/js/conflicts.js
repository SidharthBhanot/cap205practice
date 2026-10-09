import { api, params } from './api.js';
import { $, mount, icon, badge, label, date, time, escapeHTML as e, options, issueTypes, reviewStatuses, errorState, empty, modal, toast, staleNotice, run, recordDetail, pagination } from './common.js';

mount('conflicts','Verification queue','Review source evidence, record your decision, and preserve the explanation.',
  `<button class="btn" id="run">${icon('reconcile')}Run reconciliation</button>`);
let offset=0, sequence=0;
const limit=12;
async function init() {
  try {
    const courses=await api('/courses');
    $('#content').innerHTML=`<div id="freshness"></div><form class="toolbar" id="filters"><label>Verification status<select name="status">${options(reviewStatuses)}</select></label><label>Issue type<select name="conflict_type">${options(issueTypes)}</select></label><label>Course<select name="course_id">${options(courses.map(c=>({id:c.id,name:c.code+' · '+c.name})))}</select></label><label>Detection scope<select name="current_only"><option value="true">Latest run only</option><option value="false">Include historical issues</option></select></label></form><div class="filter-foot"><span id="issue-count"></span><span>Only you can resolve or dismiss an issue.</span></div><section class="panel"><div id="issues"><div class="loading">Loading verification queue…</div></div><div class="pagination" id="pagination"></div></section>`;
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
    $('#issues').innerHTML=d.items.length ? `<div class="table-wrap"><table><thead><tr><th>Issue</th><th>Source records</th><th>Verification</th><th>Last detected</th><th>Action</th></tr></thead><tbody>${d.items.map(issue=>`<tr><td>${badge(issue.conflict_type)}<span class="subline">Issue #${issue.id}${!issue.is_current?' · Historical':''}</span></td><td><strong>${e(issue.source_records[0].title || 'Untitled record')}</strong><span class="subline">${e(issue.source_records.map(r=>r.source.name+' #'+r.id).join(' · '))}</span><div class="issue-explanation">${e(issue.explanation)}</div></td><td>${badge(issue.status)}${issue.evidence_changed?'<span class="subline"><strong>Changed evidence: verify again</strong></span>':''}</td><td class="nowrap">${date(issue.last_detected_at)}</td><td><button class="btn secondary small" data-review="${issue.id}">Review</button></td></tr>`).join('')}</tbody></table></div>` : empty('No issues in this view','Run reconciliation or adjust your filters. Historical issues remain available until you explicitly review them.');
    pagination(d.total,offset,limit,next=>{offset=next;load();});
    document.querySelectorAll('[data-review]').forEach(b=>b.onclick=()=>detail(Number(b.dataset.review)).catch(error=>toast(error.message,true)));
  }catch(error){if(request===sequence)errorState(error,'#issues');}
}
async function detail(id) {
  const issue=await api('/conflicts/'+id);
  const liveIDs=issue.live_obligation_ids;
  modal({title:`Issue #${issue.id} · ${label(issue.conflict_type)}`,wide:true,submitText:'Save review decision',body:`<div class="badge-row">${badge(issue.status)}${badge(issue.conflict_type)}${!issue.is_current?'<span class="badge neutral">Not detected in the latest run</span>':''}</div><p style="margin-top:16px">${e(issue.explanation)}</p><div class="notice amber"><div><strong>Verify the original sources before deciding.</strong> This system does not choose a correct source, change a deadline, or merge records.</div></div>${issue.evidence_changed?'<div class="notice amber"><div><strong>Evidence changed after the last review.</strong> Your previous status and notes are preserved. Verify this new evidence before relying on that decision.</div></div>':''}<h3>Evidence from the latest detection</h3><div class="detail-grid">${issue.source_records.map(r=>recordDetail(r,liveIDs.includes(r.id))).join('')}</div><details class="rule-box"><summary>View current live records (${issue.current_records.length})</summary><p>These may differ from the detection snapshot if a record was edited. Run reconciliation to refresh evidence.</p><div class="detail-grid">${issue.current_records.map(r=>recordDetail(r)).join('') || '<p>The original records have been deleted. Their detection snapshots remain above.</p>'}</div></details><p class="small-text muted">First detected ${time(issue.detected_at)} · Last detected ${time(issue.last_detected_at)}${issue.reviewed_at?' · Last reviewed '+time(issue.reviewed_at):''}</p><div class="review-form form-grid"><label>Verification status<select name="status">${options(reviewStatuses,issue.status,null)}</select></label><div class="form-help">A decision changes this issue only. To correct a record, edit it separately and run reconciliation again.</div><label class="full">Resolution notes<textarea name="resolution_notes" maxlength="10000" placeholder="What did you check, and why did you make this decision?">${e(issue.resolution_notes)}</textarea></label></div>`,onSubmit:async data=>{
    await api('/conflicts/'+id+'/status',{method:'PUT',body:Object.fromEntries(data)});toast('Review saved. Original source records are unchanged.');await load();
  }});
}
$('#run').onclick=event=>run(event.currentTarget,load);
init();
