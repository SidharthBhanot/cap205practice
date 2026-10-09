import { api, params } from './api.js';
import { $, mount, icon, badge, date, escapeHTML as e, types, statuses, options, errorState, empty, modal, toast, confirmDelete, recordDetail, pagination, debounce } from './common.js';

mount('obligations','Academic obligations','Keep each source record intact, even when two sources disagree.',
  `<button class="btn secondary" id="add-course">Add course</button><button class="btn" id="add-record">${icon('plus')}Add obligation</button>`);
let courses = [], sources = [], offset = 0, sequence = 0;
const limit = 12;
function courseOptions() { return courses.map(c => ({id:c.id,name:`${c.code} · ${c.name}`})); }

async function init() {
  try {
    [courses,sources] = await Promise.all([api('/courses'),api('/sources')]);
    $('#content').innerHTML = `<form class="toolbar" id="filters"><label class="search-field">Search records<input id="search" name="q" type="search" placeholder="Title, course, description or source"></label><label>Course<select name="course_id" id="course-filter">${options(courseOptions())}</select></label><label>Type<select name="obligation_type">${options(types)}</select></label><label>Status<select name="status">${options(statuses)}</select></label><label>Deadline from<input name="deadline_from" type="date"></label><label>Deadline to<input name="deadline_to" type="date"></label><label>Sort by<select name="sort_by">${options([{id:'deadline',name:'Deadline'},{id:'title',name:'Title'},{id:'course',name:'Course'},{id:'type',name:'Type'},{id:'status',name:'Status'},{id:'recorded_at',name:'Date recorded'}],'deadline',null)}</select></label><label>Order<select name="order"><option value="asc">Ascending</option><option value="desc">Descending</option></select></label></form><div class="filter-foot"><label class="checkbox"><input type="checkbox" id="missing-only">Only missing deadlines</label><span id="record-count"></span></div><section class="panel"><div id="record-table"><div class="loading">Loading obligations…</div></div><div class="pagination" id="pagination"></div></section>`;
    $('#filters').onsubmit = event => event.preventDefault();
    $('#filters').addEventListener('change', () => { offset=0; load(); });
    $('#search').addEventListener('input',debounce(() => { offset=0; load(); }));
    $('#missing-only').onchange = () => {offset=0; load();};
    await load();
    const query = new URLSearchParams(location.search);
    if (query.has('id')) await view(Number(query.get('id')));
    else if (query.has('new')) editor();
  } catch (error) { errorState(error); }
}
async function load() {
  const request = ++sequence;
  try {
    const filters = Object.fromEntries(new FormData($('#filters')));
    const d = await api('/obligations' + params({...filters,missing_deadline:$('#missing-only').checked,offset,limit}));
    if (request !== sequence) return;
    if (offset >= d.total && offset > 0) { offset=Math.max(0,Math.floor((d.total-1)/limit)*limit); return load(); }
    $('#record-count').textContent = `${d.total} source record${d.total === 1 ? '' : 's'}`;
    $('#record-table').innerHTML = d.items.length ? `<div class="table-wrap"><table><thead><tr><th>Obligation</th><th>Course</th><th>Deadline</th><th>Source</th><th>Status</th><th>Actions</th></tr></thead><tbody>${d.items.map(r => `<tr><td><button class="text-button" data-view="${r.id}">${e(r.title || 'Untitled record')}</button><span class="subline">#${r.id} · ${e(r.obligation_type || 'Type missing')}</span></td><td>${e(r.course?.code || 'Not recorded')}</td><td class="nowrap">${r.deadline ? date(r.deadline) : badge('MISSING_DEADLINE')}</td><td><a href="sources.html?id=${r.source_id}">${e(r.source.name)}</a></td><td>${badge(r.status)}</td><td><div class="actions"><button class="text-button" data-edit="${r.id}">Edit</button><button class="text-button" data-delete="${r.id}" aria-label="Delete record ${r.id}">Delete</button></div></td></tr>`).join('')}</tbody></table></div>` : empty('No records found','Add an obligation or change your search and filters.');
    pagination(d.total,offset,limit,next => {offset=next; load();});
    document.querySelectorAll('[data-view]').forEach(b => b.onclick = () => view(Number(b.dataset.view)).catch(err => toast(err.message,true)));
    document.querySelectorAll('[data-edit]').forEach(b => b.onclick = async () => {try { editor(await api('/obligations/'+b.dataset.edit)); } catch(error){toast(error.message,true);} });
    document.querySelectorAll('[data-delete]').forEach(b => b.onclick = async () => {
      if (!await confirmDelete('Delete this obligation?','The live source record will be deleted. Existing issue evidence and review notes will remain. Run reconciliation after deleting.')) return;
      try { await api('/obligations/'+b.dataset.delete,{method:'DELETE'}); toast('Obligation deleted. Reconciliation needs a new run.'); await load(); } catch(error){toast(error.message,true);}
    });
  } catch(error) { if(request===sequence) errorState(error,'#record-table'); }
}
async function view(id) {
  const record = await api('/obligations/'+id);
  const dialog = modal({title:`Obligation #${record.id}`,body:recordDetail(record,false).replace('<span class="badge neutral">Original record deleted</span>','') + '<div class="dialog-actions"><button class="btn" id="edit-detail">Edit record</button></div>'});
  $('#edit-detail',dialog).onclick = () => editor(record);
}
function editor(record = {}) {
  if (!sources.length) {
    modal({title:'Add an information source first',body:'<p>Every obligation must trace back to a registered source.</p><a class="btn" href="sources.html?new=1">Register a source</a>'}); return;
  }
  modal({title:record.id ? `Edit obligation #${record.id}` : 'Add an obligation',submitText:record.id ? 'Save record' : 'Create record',body:`<div class="notice"><div>Copy the original source information. Leave unknown fields blank so reconciliation can flag them.</div></div><div class="form-grid"><label class="full">Original title<input name="title" maxlength="240" value="${e(record.title || '')}" placeholder="For example, Assignment 2"></label><label>Course<select name="course_id">${options(courseOptions(),record.course_id,'Not recorded')}</select></label><label>Obligation type<select name="obligation_type">${options(types,record.obligation_type,'Not recorded')}</select></label><label>Deadline<input name="deadline" type="date" value="${e(record.deadline || '')}"><span class="form-help">Calendar date as stated by this source.</span></label><label>Status<select name="status">${options(statuses,record.status || 'Planned',null)}</select></label><label class="full">Information source <span class="form-help">Required</span><select name="source_id" required>${options(sources,record.source_id || sources[0].id,null)}</select></label><label class="full">Description<textarea name="description" maxlength="20000">${e(record.description || '')}</textarea></label><label class="full">Reference URL (optional)<input name="reference_url" type="url" maxlength="2048" value="${e(record.reference_url || '')}" placeholder="https://…"></label></div>`,onSubmit:async data => {
    const payload = Object.fromEntries(data); payload.course_id = payload.course_id ? Number(payload.course_id) : null; payload.source_id = Number(payload.source_id);
    ['deadline','obligation_type','reference_url'].forEach(key => {payload[key] ||= null;});
    await api('/obligations'+(record.id ? '/'+record.id : ''),{method:record.id ? 'PUT':'POST',body:payload});
    toast('Record saved. Run reconciliation to check the latest evidence.'); await load();
  }});
}
$('#add-record').onclick = () => editor();
$('#add-course').onclick = () => modal({title:'Add a course',submitText:'Create course',body:'<div class="form-grid"><label>Course code<input name="code" required maxlength="30" placeholder="CAP205"></label><label>Course name<input name="name" required maxlength="160" placeholder="Next Gen Computing"></label></div>',onSubmit:async data => {
  await api('/courses',{method:'POST',body:Object.fromEntries(data)}); courses=await api('/courses'); $('#course-filter').innerHTML=options(courseOptions()); toast('Course created.');
}});
init();
