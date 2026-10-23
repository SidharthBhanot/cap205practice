import { api, params } from './api.js';
import { API_BASE } from './config.js';
import { $, mount, icon, badge, date, time, escapeHTML as e, options, sourceTypes, errorState, empty, modal, toast, confirmDelete, debounce, referenceLink } from './common.js';

mount('sources','Information sources','Register where each record came from. All information is entered manually.',
  `<button class="btn secondary" id="refresh-sources">Refresh</button><button class="btn" id="add-source">${icon('plus')}Add source</button>`);
let sequence=0;
$('#content').innerHTML = `<div class="notice"><div><strong>Manually registered sources.</strong> Add the LMS, notice, email or document where you found each obligation.</div></div><form class="toolbar" id="filters"><label class="search-field">Find a source<input type="search" name="q" id="search" placeholder="Search by source name"></label><label>Source type<select name="source_type">${options(sourceTypes)}</select></label></form><div class="filter-foot"><span id="source-count" role="status"></span><button type="button" class="text-button" id="clear-source-filters">Clear filters</button></div><div class="source-grid" id="source-grid" aria-busy="true"><div class="loading" role="status">Loading sources…</div></div>`;
$('#filters').onsubmit = event => event.preventDefault();
$('#filters').onchange = () => load();
$('#search').oninput = debounce(() => load());
async function load() {
  const request=++sequence;
  $('#source-grid').setAttribute('aria-busy','true');
  $('#source-count').textContent='Loading sources…';
  $('#refresh-sources').disabled=true;
  try {
    const sources=await api('/sources'+params(Object.fromEntries(new FormData($('#filters')))));
    if(request!==sequence) return;
    if(!Array.isArray(sources)) throw new Error('Unexpected sources response. Check that the frontend and backend are from the same project version.');
    $('#source-count').textContent=`${sources.length} source${sources.length===1?'':'s'} found`;
    $('#source-grid').innerHTML = sources.length ? sources.map(s => `<article class="source-card"><div class="attention-top">${badge(s.source_type)}<span class="small-text muted">Source #${s.id}</span></div><h2><button class="text-button" data-view="${s.id}">${e(s.name)}</button></h2><p>${e(s.description || 'No description recorded.')}</p>${referenceLink(s.reference_url)}<div class="source-meta"><span><strong>${s.obligation_count}</strong> obligation${s.obligation_count===1?'':'s'}</span><span>Last checked: ${date(s.last_checked_at)}</span></div><div class="source-actions"><button class="btn secondary small" data-edit="${s.id}">Edit source</button><button class="text-button" data-delete="${s.id}">Delete</button></div></article>`).join('') : empty('No sources found','Register an LMS, faculty notice, email, PDF, ERP or manual source.');
    document.querySelectorAll('[data-view]').forEach(b => b.onclick = () => view(Number(b.dataset.view)).catch(error => toast(error.message,true)));
    document.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => editor(sources.find(s => s.id===Number(b.dataset.edit))));
    document.querySelectorAll('[data-delete]').forEach(b => b.onclick = async () => {
      if(!await confirmDelete('Delete this source?','Sources referenced by obligations cannot be deleted. Existing issue snapshots remain available.'))return;
      try {await api('/sources/'+b.dataset.delete,{method:'DELETE'});toast('Source deleted.');await load();}catch(error){toast(error.message,true);}
    });
  }catch(error){
    if(request!==sequence)return;
    $('#source-count').textContent='Sources could not be loaded';
    errorState(error,'#source-grid',load);
    $('.error-state', $('#source-grid')).insertAdjacentHTML('beforeend',
      `<p class="connection-help">API address: <code>${e(API_BASE)}</code><br>${referenceLink(API_BASE+'/app/sources.html','Open Sources through FastAPI')}</p>`);
  }finally{
    if(request===sequence){$('#source-grid').setAttribute('aria-busy','false');$('#refresh-sources').disabled=false;}
  }
}
async function view(id) {
  const s=await api('/sources/'+id);
  const dialog=modal({title:s.name,body:`${badge(s.source_type)}<p class="preserve" style="margin-top:18px">${e(s.description || 'No description recorded.')}</p><p class="small-text muted">Recorded: ${time(s.recorded_at)}<br>Updated: ${time(s.updated_at)}<br>Last checked: ${s.last_checked_at ? time(s.last_checked_at) : 'Not recorded'}</p>${referenceLink(s.reference_url)}<div class="dialog-actions"><button class="btn" id="edit-source-detail">Edit source</button></div>`});
  $('#edit-source-detail',dialog).onclick=()=>editor(s);
}
function editor(source={}) {
  let localTime='';
  if(source.last_checked_at){const d=new Date(source.last_checked_at);localTime=new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);}
  modal({title:source.id ? 'Edit information source':'Register information source',submitText:source.id?'Save source':'Register source',body:`<div class="form-grid"><label class="full">Source name<input name="name" required maxlength="120" value="${e(source.name || '')}" placeholder="For example, LMS"></label><label>Source type<select name="source_type">${options(sourceTypes,source.source_type || 'LMS',null)}</select></label><label>Last checked (optional)<input type="datetime-local" name="last_checked_at" value="${localTime}"><span class="form-help">When you last verified this source, in your local time.</span></label><label class="full">Description<textarea name="description" maxlength="10000">${e(source.description || '')}</textarea></label><label class="full">Reference URL (optional)<input type="url" name="reference_url" maxlength="2048" value="${e(source.reference_url || '')}" placeholder="https://…"></label></div>`,onSubmit:async data => {
    const payload=Object.fromEntries(data); payload.reference_url ||= null;payload.last_checked_at=payload.last_checked_at ? new Date(payload.last_checked_at).toISOString():null;
    await api('/sources'+(source.id?'/'+source.id:''),{method:source.id?'PUT':'POST',body:payload});
    // Make the newly saved source visible even if a previous search/type filter
    // would exclude it. The records still come only from a successful API read.
    $('#filters').reset();
    toast('Source saved.');await load();
  }});
}
$('#add-source').onclick=()=>editor();
$('#refresh-sources').onclick=()=>load();
$('#clear-source-filters').onclick=()=>{$('#filters').reset();load();};
async function init() {
  await load();
  const p=new URLSearchParams(location.search);
  if(p.has('id')) {
    try { await view(Number(p.get('id'))); }
    catch(error) { toast(error.message,true); }
  } else if(p.has('new')) editor();
}
init();
