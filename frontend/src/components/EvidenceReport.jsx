import React from 'react';
import Icon from './Icon.jsx';
export default function EvidenceReport({result,edited=false}){
  const report=result?.evidenceSummary?.qualityReport;
  if(!report)return <div className="report-empty"><Icon name="shield" size={30}/><h3>No evidence report attached</h3><p>Generate a prompt from the current selection. Restored text remains editable, but it does not establish a live measurement.</p></div>;
  const c=report.coverage;
  return <section className="evidence-report" aria-label="Prompt Quality & Evidence Report"><div className="report-heading"><Icon name="shield"/><div><h3>Prompt Quality & Evidence Report</h3><p>Evidence coverage, never an accuracy score.{edited?' Your edits do not change this generation snapshot.':''}</p></div></div><div className="coverage-stats"><div><strong>{c.describedNodes}<small> / {c.collectedNodes}</small></strong><span>Nodes described / collected</span></div><div><strong>{c.computedStyleEntries}</strong><span>Computed CSS entries</span></div><div><strong>{c.flaggedProperties}</strong><span>Sanitization / length flags</span></div><div><strong>{c.truncated?'Bounded':'No flag'}</strong><span>{c.truncated?'Evidence omissions flagged':'No truncation flag reported'}</span></div></div>
    {c.selectedOmitted&&<p className="error" role="alert">Selected-node evidence is incomplete. Inspect a smaller target before using this prompt.</p>}
    {[['observed','Measured & observed','observed'],['inferred','Inferred & recommended','inferred'],['missing','Missing & unknown','missing']].map(([key,title,className])=><details className={`evidence-group ${className}`} key={key} open><summary>{title}</summary><ul>{report[key].map((line,i)=><li key={i}>{line}</li>)}</ul></details>)}
    <details className="evidence-group" open><summary>Warnings & limitations</summary><ul>{[...new Set([...report.warnings,...report.limitations])].map((line,i)=><li key={i}>{line}</li>)}</ul></details><p className="fine-print">Renderer omitted {c.rendererOmittedNodes} nodes; invalid paths {c.invalidPaths}. Collection and byte-budget omissions can be additional. Source context is valid for the last generation only.</p>
  </section>;
}
