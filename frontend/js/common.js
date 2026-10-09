import { api } from './api.js';
import { API_BASE } from './config.js';

export const $ = (selector, scope = document) => scope.querySelector(selector);
export const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const types = ['Assignment','Quiz','Examination','Project','Other'];
export const statuses = ['Planned','In Progress','Completed','Cancelled'];
export const reviewStatuses = ['Needs Verification','Under Review','Resolved','Dismissed'];
export const issueTypes = ['DEADLINE_CONFLICT','DUPLICATE','MISSING_DEADLINE','INCOMPLETE_INFORMATION','OUTDATED_INFORMATION'];
export const sourceTypes = ['LMS','ERP','Faculty Notice','Email','PDF','Manual'];
export const classifications = ['MATCH','POTENTIAL_MATCH','CONFLICT','UNRELATED'];
export const label = value => ({MATCH:'Match',POTENTIAL_MATCH:'Potential match',CONFLICT:'Conflict',UNRELATED:'Unrelated',DEADLINE_CONFLICT:'Deadline conflict',DUPLICATE:'Duplicate',MISSING_DEADLINE:'Missing deadline',INCOMPLETE_INFORMATION:'Incomplete information',OUTDATED_INFORMATION:'Possibly outdated'}[value] || value);
export function badge(value) {
  const style = ['CONFLICT','DEADLINE_CONFLICT'].includes(value) ? 'red'
    : ['Needs Verification','POTENTIAL_MATCH','MISSING_DEADLINE','OUTDATED_INFORMATION','INCOMPLETE_INFORMATION'].includes(value) ? 'amber'
    : ['MATCH','Resolved','Completed'].includes(value) ? 'green'
    : ['DUPLICATE','Under Review','In Progress'].includes(value) ? 'blue' : 'neutral';
  return `<span class="badge ${style}">${escapeHTML(label(value))}</span>`;
}
export function date(value) {
  if (!value) return 'Not recorded';
  return new Date(value.length === 10 ? value + 'T12:00:00' : value).toLocaleDateString('en-GB', { day:'numeric', month:'short', year:'numeric' });
}
export function time(value) {
  return value ? new Date(value).toLocaleString('en-GB', { dateStyle:'medium', timeStyle:'short' }) : 'Not yet run';
}
export function options(values, selected = '', first = 'All') {
  return `${first === null ? '' : `<option value="">${escapeHTML(first)}</option>`}` + values.map(value => {
    const id = typeof value === 'object' ? value.id : value;
    const title = typeof value === 'object' ? value.name : label(value);
    return `<option value="${escapeHTML(id)}" ${String(selected) === String(id) ? 'selected' : ''}>${escapeHTML(title)}</option>`;
  }).join('');
}
const paths = {
  grid:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  records:'<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h4"/>',
  sources:'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 4 16 4 16 0V5M4 12v7c0 4 16 4 16 0v-7"/>',
  reconcile:'<path d="M4 7h16m-3-3 3 3-3 3M20 17H4m3-3-3 3 3 3"/>',
  alert:'<path d="m12 3 10 18H2L12 3Z"/><path d="M12 9v5m0 3v.2"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  check:'<path d="m5 12 4 4L19 6"/>',
  menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
};
export function icon(name) { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.records}</svg>`; }

export function mount(page, title, subtitle, actions = '') {
  const navigation = [['dashboard','index.html','Overview','grid'],['obligations','obligations.html','Obligations','records'],['sources','sources.html','Information sources','sources'],['results','results.html','Reconciliation','reconcile'],['conflicts','conflicts.html','Verification queue','alert']];
  $('#shell').innerHTML = `<a class="skip-link" href="#main">Skip to content</a><aside class="sidebar" id="sidebar"><a href="index.html" class="brand"><span class="brand-mark" aria-hidden="true"></span><span>Academic<br>Reconcile<small>CAP205 PROJECT</small></span></a><div class="nav-label">WORKSPACE</div><nav class="nav-list" aria-label="Main navigation">${navigation.map(([id,href,name,ic]) => `<a href="${href}" class="${page === id ? 'active' : ''}" ${page === id ? 'aria-current="page"' : ''}>${icon(ic)}${name}</a>`).join('')}</nav><div class="sidebar-foot"><span class="local-pill">Local prototype</span><strong>Evidence before assumptions.</strong>Records are entered manually.<br>Every decision stays with you.</div></aside><div class="workspace"><header class="topbar"><div class="crumb"><button class="menu-toggle" aria-label="Toggle navigation" aria-expanded="false">${icon('menu')}</button><strong>Student workspace</strong><span>/</span><span>${navigation.find(x => x[0] === page)[2]}</span></div><div class="topbar-right"><span id="connection">Checking API…</span><span id="today">${date(new Date().toISOString())}</span><span class="avatar" aria-label="Academic workspace">AC</span></div></header><main class="main" id="main"><div class="page-head"><div><div class="eyebrow">Student Academic Obligation Reconciliation System</div><h1>${escapeHTML(title)}</h1><p>${escapeHTML(subtitle)}</p></div><div class="head-actions">${actions}</div></div><div id="content"><div class="loading" role="status">Loading your workspace…</div></div><footer class="app-footer"><span>CAP205 · Next Gen Computing</span><span>Manual source records · Explainable rules · Human verification</span></footer></main></div><div class="toast-region" aria-live="polite" id="toasts"></div><dialog class="dialog" id="modal" aria-labelledby="modal-title"></dialog><dialog class="dialog" id="confirm-modal" aria-labelledby="confirm-title"></dialog>`;
  $('.menu-toggle').onclick = () => {
    const open = $('#sidebar').classList.toggle('open');
    $('.menu-toggle').setAttribute('aria-expanded', String(open));
  };
  document.addEventListener('click', event => {
    if (!event.target.closest('.sidebar, .menu-toggle') && $('#sidebar').classList.contains('open')) {
      $('#sidebar').classList.remove('open'); $('.menu-toggle').setAttribute('aria-expanded','false');
    }
  });
  api('/health').then(() => { $('#connection').textContent = 'API connected'; }).catch(() => { $('#connection').textContent = 'API unavailable'; });
}

export function toast(message, error = false) {
  const item = document.createElement('div'); item.className = 'toast' + (error ? ' error' : ''); item.textContent = message;
  $('#toasts').append(item); setTimeout(() => item.remove(), error ? 9000 : 5500);
}
export function errorState(error, target = '#content') {
  $(target).innerHTML = `<div class="error-state" role="alert"><strong>Unable to load this view</strong><p>${escapeHTML(error.message)}</p><button class="btn secondary" id="retry">Try again</button></div>`;
  $('#retry').onclick = () => location.reload();
}
export function empty(title, explanation, action = '') { return `<div class="empty"><h3>${escapeHTML(title)}</h3><p>${escapeHTML(explanation)}</p>${action}</div>`; }
export function staleNotice(stale, lastRun) {
  return stale ? `<div class="notice amber">${icon('alert')}<div><strong>${lastRun ? 'Records or rules have changed since the last run.' : 'Reconciliation has not been run yet.'}</strong><br>${lastRun ? 'Results below are a previous snapshot. Run reconciliation to review the latest evidence.' : 'Run reconciliation to check duplicates, deadline conflicts and missing information.'}</div></div>` : `<div class="notice">${icon('check')}<div>Reconciled ${escapeHTML(time(lastRun))}. Source records remain unchanged.</div></div>`;
}
export async function run(button, onComplete) {
  const previous = button.innerHTML; button.disabled = true; button.textContent = 'Reconciling…';
  try { const report = await api('/reconcile', { method:'POST' }); toast(`Compared ${report.candidate_pairs} pairs. ${report.new_issues} new issues recorded.`); await onComplete(report); }
  catch (error) { toast(error.message, true); }
  finally { button.disabled = false; button.innerHTML = previous; }
}

export function modal({ title, body, onSubmit, submitText = 'Save changes', wide = false }) {
  const dialog = $('#modal'); dialog.classList.toggle('wide', wide);
  dialog.innerHTML = `<div class="dialog-head"><h2 id="modal-title">${escapeHTML(title)}</h2><button type="button" class="close-dialog" aria-label="Close dialog">×</button></div><div class="dialog-body">${onSubmit ? '<form id="modal-form">' : ''}${body}${onSubmit ? `<div class="form-error" role="alert"></div><div class="dialog-actions"><button class="btn secondary" type="button" data-close>Cancel</button><button class="btn" type="submit">${escapeHTML(submitText)}</button></div></form>` : ''}</div>`;
  dialog.querySelectorAll('.close-dialog,[data-close]').forEach(button => { button.onclick = () => dialog.close(); });
  if (onSubmit) $('#modal-form').onsubmit = async event => {
    event.preventDefault(); const button = $('button[type=submit]', dialog); const error = $('.form-error', dialog);
    error.textContent = ''; button.disabled = true;
    try { await onSubmit(new FormData(event.target)); dialog.close(); }
    catch (err) { error.textContent = err.message; }
    finally { button.disabled = false; }
  };
  if (!dialog.open) dialog.showModal();
  return dialog;
}
export function confirmDelete(title, explanation) {
  return new Promise(resolve => {
    const dialog = $('#confirm-modal');
    dialog.innerHTML = `<div class="dialog-head"><h2 id="confirm-title">${escapeHTML(title)}</h2></div><div class="dialog-body"><p>${escapeHTML(explanation)}</p><div class="dialog-actions"><button class="btn secondary" data-cancel>Cancel</button><button class="btn danger" data-delete>Delete</button></div></div>`;
    let answer = false;
    dialog.onclose = () => resolve(answer);
    $('[data-cancel]', dialog).onclick = () => dialog.close();
    $('[data-delete]', dialog).onclick = () => { answer = true; dialog.close(); };
    dialog.showModal(); $('[data-cancel]', dialog).focus();
  });
}
export function referenceLink(url, title = 'Open source reference') {
  if (!url || !/^https?:\/\//i.test(url)) return '';
  return `<a href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(title)}</a>`;
}
export function recordDetail(record, live = true) {
  return `<article class="record-detail"><div class="badge-row">${badge(record.source.source_type)}<span class="badge neutral">Record #${record.id}</span></div><h3>${escapeHTML(record.title || 'Untitled record')}</h3><p class="muted">${escapeHTML(record.course ? record.course.code + ' · ' + record.course.name : 'Course not recorded')}</p><dl><dt>Deadline</dt><dd><strong>${date(record.deadline)}</strong></dd><dt>Type</dt><dd>${escapeHTML(record.obligation_type || 'Not recorded')}</dd><dt>Status</dt><dd>${escapeHTML(record.status)}</dd><dt>Source</dt><dd><a href="sources.html?id=${record.source_id}">${escapeHTML(record.source.name)}</a></dd><dt>Recorded</dt><dd>${time(record.recorded_at)}</dd><dt>Updated</dt><dd>${time(record.updated_at)}</dd><dt>Source checked</dt><dd>${record.source.last_checked_at ? time(record.source.last_checked_at) : 'Not recorded'}</dd></dl>${record.description ? `<p>${escapeHTML(record.description)}</p>` : ''}<p class="muted">${escapeHTML(record.source.description)}</p><div class="actions">${referenceLink(record.reference_url || record.source.reference_url)}${live ? `<a class="btn secondary small" href="obligations.html?id=${record.id}">View current record</a>` : '<span class="badge neutral">Original record deleted</span>'}</div></article>`;
}
export function pagination(total, offset, limit, callback, target = '#pagination') {
  $(target).innerHTML = `<span>${total ? `${offset + 1}–${Math.min(offset + limit, total)} of ${total}` : '0 records'}</span><div class="actions"><button class="btn secondary small" data-prev ${offset === 0 ? 'disabled' : ''}>Previous</button><button class="btn secondary small" data-next ${offset + limit >= total ? 'disabled' : ''}>Next</button></div>`;
  $('[data-prev]', $(target)).onclick = () => callback(Math.max(0, offset - limit));
  $('[data-next]', $(target)).onclick = () => callback(offset + limit);
}
export function debounce(callback, delay = 250) { let timer; return (...args) => { clearTimeout(timer); timer = setTimeout(() => callback(...args), delay); }; }
export function docsURL() { return API_BASE + '/docs'; }
