import { api, params } from './api.js';
import { $, mount, icon, badge, label, date, time, escapeHTML as e, options, classifications, issueTypes, errorState, empty, staleNotice, run, pagination } from './common.js';

mount('results','Reconciliation results','Inspect the evidence behind each relationship. Similarity is a rule score, not a probability.',
  `<button class="btn" id="run">${icon('reconcile')}Run reconciliation</button>`);
let offset=0, sequence=0;
const limit=10;
async function init() {
  try {
    const [courses,config]=await Promise.all([api('/courses'),api('/reconciliation/config')]);
    $('#content').innerHTML=`<div id="freshness"></div><form class="toolbar" id="filters"><label>Classification<select name="classification">${options(classifications)}</select></label><label>Course<select name="course_id">${options(courses.map(c=>({id:c.id,name:c.code+' · '+c.name})))}</select></label><label>Issue type<select name="issue_type">${options(issueTypes)}</select></label></form><details class="rule-box"><summary>How these comparisons are made</summary><p>${e(config.similarity_method)}. Strong threshold: <strong>${config.match_threshold}</strong>; potential threshold: <strong>${config.potential_threshold}</strong>. Course, type, distinguishing title details and recorded deadlines also matter. No source is ranked as more trustworthy.</p><p>Candidate selection: ${e(config.blocking_method)}. Unexamined pairs are skipped, not certified unrelated. ${e(config.deadline_precision)}.</p><p>Thresholds are configurable through the backend environment. An old active record may be flagged after ${config.stale_days} days without an update or source check.</p></details><div class="filter-foot"><span id="result-count"></span><span id="run-summary"></span></div><div class="result-list" id="results"><div class="loading">Loading comparisons…</div></div><div class="pagination" id="pagination"></div>`;
    $('#filters').onsubmit=event=>event.preventDefault();$('#filters').onchange=()=>{offset=0;load();};
    await load();
  }catch(error){errorState(error);}
}
function recordMini(record) {
  return `<div class="record-mini"><div class="mini-source">${e(record.source.name)} · RECORD #${record.id}</div><h3><a href="obligations.html?id=${record.id}">${e(record.title || 'Untitled record')}</a></h3><p>${e(record.course ? record.course.code+' · '+record.course.name:'Course not recorded')}</p><p>${e(record.obligation_type || 'Type not recorded')} · <strong>${date(record.deadline)}</strong></p></div>`;
}
async function load() {
  const request=++sequence;
  try {
    const d=await api('/reconciliation/results'+params({...Object.fromEntries(new FormData($('#filters'))),offset,limit}));
    if(request!==sequence)return;
    $('#freshness').innerHTML=staleNotice(d.is_stale,d.summary.compared_at);
    $('#result-count').textContent=`${d.total} comparison${d.total===1?'':'s'} found`;
    $('#run-summary').textContent=d.summary.compared_at ? `${d.summary.candidate_pairs} pairs checked · ${d.summary.skipped_pairs} skipped`:'No reconciliation run yet';
    $('#results').innerHTML=d.items.length ? d.items.map(result=>`<article class="result-card"><div class="result-header">${badge(result.classification)}${badge(result.verification_status)}<span class="score">Title similarity ${Math.round(result.title_similarity*100)}% · ${time(result.compared_at)}</span></div><div class="record-pair">${result.source_records.map(recordMini).join('')}</div><div class="result-reason"><p><strong>Why:</strong> ${e(result.reason)}</p>${result.conflicts.length ? `<div class="actions">${result.conflicts.map(i=>`<a class="btn secondary small" href="conflicts.html?id=${i.id}">#${i.id} · ${label(i.conflict_type)}</a>`).join('')}</div>`:'<p class="muted">No issue created for this comparison.</p>'}</div></article>`).join(''):empty('No comparisons to show',d.summary.compared_at?'Try different filters. Distinct records may have been skipped by candidate selection.':'Add records and run reconciliation to compare them.');
    pagination(d.total,offset,limit,next=>{offset=next;load();});
  }catch(error){if(request===sequence)errorState(error,'#results');}
}
$('#run').onclick=event=>run(event.currentTarget,()=>{offset=0;return load();});
init();
