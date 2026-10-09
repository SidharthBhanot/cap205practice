import { api } from './api.js';
import { $, mount, icon, badge, label, escapeHTML as e, date, time, empty, errorState, staleNotice, run } from './common.js';

mount('dashboard','Academic overview','One place to compare records and review what needs verification.',
  `<a href="obligations.html?new=1" class="btn secondary">${icon('plus')}Add obligation</a><button id="run" class="btn">${icon('reconcile')}Run reconciliation</button>`);

async function load() {
  try {
    const d = await api('/dashboard');
    const metrics = [
      ['Total obligations',d.total_obligations,'Original source records','records',''],
      ['Information sources',d.total_sources,'Manually registered','sources',''],
      ['Potential duplicates',d.potential_duplicates,'Open pairs to verify','reconcile','pending'],
      ['Unresolved conflicts',d.unresolved_conflicts,'Open material disagreements','alert','alert'],
      ['Incomplete records',d.incomplete_records,'Missing key information','records','pending']
    ];
    const counts = d.summary.classifications || {MATCH:0,POTENTIAL_MATCH:0,CONFLICT:0,UNRELATED:0};
    const total = d.summary.candidate_pairs || 0;
    $('#content').innerHTML = `${d.synthetic_data ? '<div class="notice small-text"><div><strong>Synthetic demonstration workspace.</strong> These examples contain no real student information. LMS, email and PDF entries are recorded manually.</div></div>' : ''}${staleNotice(d.is_stale,d.last_reconciled_at)}
      <div class="metrics">${metrics.map(([title,value,caption,ic,style]) => `<div class="metric ${style}"><div class="metric-icon">${icon(ic)}</div><div class="metric-label">${title}</div><div class="metric-number mono">${value}</div><div class="metric-caption">${caption}</div></div>`).join('')}</div>
      <div class="dashboard-grid"><section class="panel"><div class="panel-head"><h2>Needs your attention</h2><a href="conflicts.html" class="small-text">View queue (${d.issues_needing_attention})</a></div>${d.priority_issues.length ? d.priority_issues.map(issue => `<article class="attention-item"><div class="attention-top">${badge(issue.conflict_type)}<a class="small-text" href="conflicts.html?id=${issue.id}">Review issue #${issue.id}</a></div><h3>${e(issue.source_records[0].title || 'Untitled source record')}</h3><p>${e(issue.source_records[0].course?.name || 'Course not recorded')} · ${issue.record_ids?.length || issue.related_obligation_ids.length} source record${issue.related_obligation_ids.length === 1 ? '' : 's'}</p>${issue.conflict_type === 'DEADLINE_CONFLICT' ? `<div class="due-comparison">${issue.source_records.map(r => `<span><small>${e(r.source.name)}</small><strong>${date(r.deadline)}</strong></span>`).join('')}</div>` : `<p>${e(issue.explanation)}</p>`}</article>`).join('') : empty('No open issues detected', d.last_reconciled_at ? 'Review the reconciliation results for the evidence behind each comparison.' : 'Run reconciliation to check your source records.')}</section>
      <section class="panel"><div class="panel-head"><h2>Reconciliation breakdown</h2><span class="badge neutral">${total} pairs</span></div><div class="panel-content">${Object.entries(counts).map(([name,count]) => `<div class="bar-row"><div class="bar-label"><span>${label(name)}</span><strong>${count}</strong></div><div class="bar-track"><div class="bar-value ${name === 'CONFLICT' ? 'red' : name === 'POTENTIAL_MATCH' ? 'blue' : name === 'UNRELATED' ? 'neutral' : ''}" style="width:${total ? count / total * 100 : 0}%"></div></div></div>`).join('')}<div class="run-meta"><p><strong>${d.summary.skipped_pairs ?? 0}</strong> irrelevant pairs skipped by candidate rules.</p><p>Last run<br><strong>${time(d.last_reconciled_at)}</strong></p><a href="results.html">Inspect comparisons</a></div></div></section></div>
      <section class="panel"><div class="panel-head"><h2>Recently recorded</h2><a href="obligations.html" class="small-text">All obligations</a></div>${d.recent_obligations.length ? `<div class="table-wrap"><table><thead><tr><th>Obligation</th><th>Course</th><th>Deadline</th><th>Source</th><th>Status</th></tr></thead><tbody>${d.recent_obligations.map(r => `<tr><td><a class="title-link" href="obligations.html?id=${r.id}">${e(r.title || 'Untitled record')}</a><span class="subline">#${r.id} · ${e(r.obligation_type || 'Type missing')}</span></td><td>${e(r.course?.code || 'Not recorded')}</td><td class="nowrap">${r.deadline ? date(r.deadline) : badge('MISSING_DEADLINE')}</td><td><a href="sources.html?id=${r.source_id}">${e(r.source.name)}</a></td><td>${badge(r.status)}</td></tr>`).join('')}</tbody></table></div>` : empty('No obligations yet','Register an information source, then record your first academic obligation.','<a class="btn" href="sources.html">Add an information source</a>')}</section>`;
  } catch (error) { errorState(error); }
}
$('#run').onclick = event => run(event.currentTarget,load);
load();
