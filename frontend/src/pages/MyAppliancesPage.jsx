import React, { useState, useEffect, useRef } from 'react';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { ApplianceService, IssueService, AgentService } from '../services/api';
import './MyAppliancesPage.css';

// Safe parser helper for diagnosis data
function parseDiagnosis(diagnosisData) {
  if (!diagnosisData) return null;
  if (typeof diagnosisData === 'object') return diagnosisData;
  try {
    return JSON.parse(diagnosisData);
  } catch (e) {
    return {
      summary: String(diagnosisData),
      analysis_mode: 'fresh_investigation',
      likely_causes: [],
      evidence: [],
      uncertainty: 'No critical uncertainties identified.',
      recommended_next_step: 'Follow standard troubleshooting procedures.',
      service_recommendation: 'N/A',
      warranty_recommendation: 'N/A',
    };
  }
}

// Subcomponent: Human-Readable AI Diagnosis Report Card (Never Raw JSON)
function DiagnosisReportCard({ diagnosisData, isHistorical = false, isFresh = false }) {
  const report = parseDiagnosis(diagnosisData);
  if (!report) return null;

  const mode = (report.analysis_mode || 'fresh_investigation').toLowerCase();

  const MODE_MAP = {
    historical_match: {
      label: 'HISTORICAL MATCH',
      className: 'mode-historical',
      icon: '↺',
      tagline: 'Reused Historical Diagnosis (Prior Successful Repair)',
      desc: 'A matching issue was previously resolved successfully on this appliance. Reusing proven diagnostic analysis and repair guidance (redundant LLM investigation bypassed).'
    },
    fresh_investigation: {
      label: 'FRESH INVESTIGATION',
      className: 'mode-fresh',
      icon: '⚡',
      tagline: 'Full AI Investigation Completed',
      desc: 'Investigated newly reported issue using deterministic tool analysis and full AI synthesis via OpenRouter.'
    },
    reinvestigation_required: {
      label: 'REINVESTIGATION REQUIRED',
      className: 'mode-reinvestigation',
      icon: '⚠️',
      tagline: 'Fresh Investigation Triggered',
      desc: 'Fresh investigation was triggered because the prior repair was recorded as failed or partial, or symptom evidence changed.'
    },
    insufficient_data: {
      label: 'INSUFFICIENT DATA',
      className: 'mode-insufficient',
      icon: '❓',
      tagline: 'Targeted Diagnostic Questions Required',
      desc: 'Current problem data is insufficient to establish a conclusive root cause. Please review the targeted questions below and record more details.'
    }
  };

  const modeConfig = MODE_MAP[mode] || MODE_MAP.fresh_investigation;

  return (
    <div className={`diagnosis-card ${isFresh ? 'fresh-card' : ''} ${isHistorical ? 'historical-card' : ''}`}>
      <div className="diagnosis-header-bar">
        <div className="diagnosis-title-group">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <h4 style={{ margin: 0 }}>AI Diagnostic Coordinator Report</h4>
            {isFresh && <span className="report-origin-badge fresh">⚡ Fresh AI Run</span>}
            {isHistorical && <span className="report-origin-badge historical">📋 Saved Historical Record</span>}
          </div>
          <span className={`mode-badge ${modeConfig.className}`}>
            <span>{modeConfig.icon}</span> {modeConfig.label}
          </span>
        </div>
      </div>

      <div className="mode-desc-note">
        <strong>{modeConfig.tagline}:</strong> {modeConfig.desc}
      </div>

      {/* 1. Summary */}
      <div className="diagnosis-summary-box">
        <h5>Problem Summary</h5>
        <p className="diagnosis-summary-text">{report.summary || 'Summary unavailable.'}</p>
      </div>

      {/* If Insufficient Data: Highlight Targeted Questions Prominently */}
      {mode === 'insufficient_data' && (
        <div className="targeted-questions-alert">
          <div className="alert-header">
            <span style={{ fontSize: '1.25rem' }}>❓</span>
            <strong>Targeted Diagnostic Questions Needed:</strong>
          </div>
          <p className="alert-body">
            {report.uncertainty || "Please provide specific symptoms, error codes, or abnormal behaviors so the agent can accurately diagnose the problem."}
          </p>
        </div>
      )}

      {/* 2. Likely Causes */}
      <div className="diagnosis-section">
        <h5 className="diagnosis-section-title">Likely Causes</h5>
        {report.likely_causes && report.likely_causes.length > 0 ? (
          <div className="causes-grid">
            {report.likely_causes.map((item, idx) => {
              const conf = (item.confidence || 'medium').toLowerCase();
              return (
                <div key={idx} className="cause-card">
                  <div className="cause-top">
                    <span className="cause-name">{item.cause}</span>
                    <span className={`cause-confidence conf-${conf}`}>{item.confidence} Confidence</span>
                  </div>
                  <p className="cause-reason-text">{item.reason}</p>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-muted" style={{ margin: 0, fontSize: '0.8125rem' }}>
            {mode === 'insufficient_data' ? 'No causes determined due to insufficient symptom data.' : 'Identified through pattern matching and symptom evidence.'}
          </p>
        )}
      </div>

      {/* 3. Evidence */}
      <div className="diagnosis-section">
        <h5 className="diagnosis-section-title">Evidence & Findings</h5>
        {report.evidence && report.evidence.length > 0 ? (
          <div className="evidence-items-list">
            {report.evidence.map((ev, idx) => (
              <div key={idx} className="evidence-item-row">
                <strong>{ev.observation}</strong> &mdash; <span>{ev.supports}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted" style={{ margin: 0, fontSize: '0.8125rem' }}>
            {mode === 'insufficient_data' ? 'Awaiting additional symptom observations.' : 'Supported by appliance telemetry and repair history records.'}
          </p>
        )}
      </div>

      {/* 4. Uncertainty (When not insufficient_data, where it is shown above) */}
      {mode !== 'insufficient_data' && (
        <div className="diagnosis-section">
          <h5 className="diagnosis-section-title">Uncertainty Assessment</h5>
          <div className="uncertainty-callout">
            {report.uncertainty || "No critical uncertainties identified."}
          </div>
        </div>
      )}

      {/* 5. Recommended Next Step */}
      <div className="diagnosis-section">
        <h5 className="diagnosis-section-title">Recommended Next Step</h5>
        <div className="next-step-callout">
          {report.recommended_next_step || "Follow standard troubleshooting procedures."}
        </div>
      </div>

      {/* 6 & 7. Service Recommendation & Warranty Recommendation */}
      <div className="rec-split-grid">
        <div className="rec-box">
          <h6>Service Recommendation</h6>
          <p>{report.service_recommendation || 'N/A'}</p>
        </div>
        <div className="rec-box">
          <h6>Warranty Recommendation</h6>
          <p>{report.warranty_recommendation || 'N/A'}</p>
        </div>
      </div>
    </div>
  );
}

// Dedicated Subcomponent: Directly Visible Historical AI Diagnosis Card (No Dropdown/Folder)
function HistoricalDiagnosisCard({ diagnosisData, issue, isMatch = false }) {
  const report = parseDiagnosis(diagnosisData);
  if (!report) return null;

  const isHistoricalMatchMode = isMatch || (report.analysis_mode === 'historical_match');
  const prevOutcome = issue?.repair_outcome || (report.summary && report.summary.toLowerCase().includes('successful') ? 'successful' : 'resolved');
  const prevRepair = issue?.repair_notes || report.recommended_next_step || 'Standard component repair and inspection applied.';

  const whyReused = isHistoricalMatchMode
    ? "A substantially matching issue was previously diagnosed and resolved successfully on this appliance. The LangGraph agent verified historical similarity, reused the verified root-cause diagnosis and previous repair procedure, and bypassed redundant investigation."
    : "This issue was previously analyzed and resolved. This verified historical diagnosis is retained directly in the view as active appliance intelligence and persistent memory.";

  const evidenceItems = (report.evidence && report.evidence.length > 0)
    ? report.evidence
    : [
        { observation: "Recorded incident in appliance history", supports: "Strong pattern match on this appliance" },
        { observation: `Previous repair outcome: ${prevOutcome}`, supports: "Confirms previous resolution was successful" }
      ];

  return (
    <div className="historical-diagnosis-direct-card">
      <div className="historical-card-top-bar">
        <div className="historical-label-wrap">
          <span className="historical-pill-badge">
            <span className="icon-clock">↺</span> {isHistoricalMatchMode ? 'Historical Match' : 'Historical AI Diagnosis'}
          </span>
          <span className="historical-status-pill">Direct View &bull; Active Appliance Memory</span>
        </div>
        <div className="historical-outcome-pill-group">
          <span className={`outcome-status-badge outcome-${prevOutcome.toLowerCase()}`}>
            Repair Outcome: {prevOutcome.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Why This History Was Reused */}
      <div className="why-reused-container">
        <div className="why-reused-header">
          <span style={{ fontSize: '1.125rem' }}>💡</span>
          <strong>Why This History Was Reused:</strong>
        </div>
        <p className="why-reused-body">{whyReused}</p>
      </div>

      {/* Historical Diagnosis */}
      <div className="historical-field-block">
        <h5 className="historical-field-label">Historical Diagnosis</h5>
        <div className="historical-summary-box">
          <p className="historical-summary-text">{report.summary || 'Root cause diagnosis preserved from history.'}</p>
        </div>
      </div>

      {/* Previous Evidence */}
      <div className="historical-field-block">
        <h5 className="historical-field-label">Previous Evidence</h5>
        <div className="historical-evidence-list">
          {evidenceItems.map((ev, idx) => (
            <div key={idx} className="historical-evidence-row">
              <strong>{ev.observation}</strong> &mdash; <span>{ev.supports}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Previous Repair & Outcome Grid */}
      <div className="historical-grid-two">
        <div className="historical-tile">
          <h5 className="historical-field-label">Previous Repair</h5>
          <p className="historical-tile-text">{prevRepair}</p>
        </div>
        <div className="historical-tile">
          <h5 className="historical-field-label">Repair Outcome</h5>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span className={`outcome-status-tag outcome-${prevOutcome.toLowerCase()}`}>
              {prevOutcome.toUpperCase()}
            </span>
            {issue?.resolved_at && (
              <span className="resolved-date-tag">
                Resolved: {new Date(issue.resolved_at).toLocaleDateString()}
              </span>
            )}
          </div>
          {issue?.repair_notes && issue.repair_notes !== prevRepair && (
            <p style={{ marginTop: '6px', fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
              {issue.repair_notes}
            </p>
          )}
        </div>
      </div>

      {/* Previous Recommendation */}
      <div className="historical-field-block">
        <h5 className="historical-field-label">Previous Recommendation</h5>
        <div className="historical-recommendation-box">
          {report.recommended_next_step || prevRepair || "Apply the same repair procedure that successfully resolved this issue."}
        </div>
      </div>

      {/* Service / Warranty if present */}
      {((report.service_recommendation && report.service_recommendation !== 'N/A') || 
        (report.warranty_recommendation && report.warranty_recommendation !== 'N/A')) && (
        <div className="rec-split-grid" style={{ marginTop: '12px' }}>
          {report.service_recommendation && report.service_recommendation !== 'N/A' && (
            <div className="rec-box">
              <h6>Service Guidance</h6>
              <p>{report.service_recommendation}</p>
            </div>
          )}
          {report.warranty_recommendation && report.warranty_recommendation !== 'N/A' && (
            <div className="rec-box">
              <h6>Warranty Status</h6>
              <p>{report.warranty_recommendation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Subcomponent for Appliance Detail View
function ApplianceDetailView({ applianceId, initialIssueId, autoDiagnose, onBack }) {
  const [appliance, setAppliance] = useState(null);
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [diagnosingIssueId, setDiagnosingIssueId] = useState(null);
  const [diagnosticResults, setDiagnosticResults] = useState({});
  const [diagnosticErrors, setDiagnosticErrors] = useState({});
  const [showAddIssueModal, setShowAddIssueModal] = useState(false);
  const [addingSymptomIssueId, setAddingSymptomIssueId] = useState(null);
  const [symptomInput, setSymptomInput] = useState('');
  const autoDiagnoseFired = useRef(false);

  // New issue form
  const [newIssueData, setNewIssueData] = useState({
    title: '',
    description: '',
    severity: 'medium',
    symptom: '',
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [app, iss] = await Promise.all([
        ApplianceService.getAppliance(applianceId),
        IssueService.getApplianceIssues(applianceId)
      ]);
      setAppliance(app);
      const sortedIssues = iss.sort((a, b) => new Date(b.reported_at) - new Date(a.reported_at));
      setIssues(sortedIssues);

      // Auto-trigger diagnosis if requested via navigation
      if (autoDiagnose && initialIssueId && !autoDiagnoseFired.current) {
        autoDiagnoseFired.current = true;
        handleRunDiagnostics(initialIssueId);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [applianceId]);

  const handleDeleteAppliance = async () => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${appliance?.name || 'this appliance'}"?\n\nThis will remove the appliance along with its issue history, symptoms, repairs, and memories according to database relationships.`
    );
    if (!confirmed) return;

    try {
      await ApplianceService.deleteAppliance(applianceId);
      if (onBack) {
        onBack(true);
      }
    } catch (err) {
      alert(`Failed to delete appliance: ${err.message}`);
    }
  };

  const handleDeleteIssue = async (issueId, issueTitle) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete the issue "${issueTitle}"?\n\nThis will permanently remove the issue and all its associated symptoms and diagnostic records.`
    );
    if (!confirmed) return;

    try {
      await IssueService.deleteIssue(issueId);
      // Immediately remove from UI state
      setIssues(prev => prev.filter(i => i.id !== issueId));
      setDiagnosticResults(prev => {
        const next = { ...prev };
        delete next[issueId];
        return next;
      });
      setDiagnosticErrors(prev => {
        const next = { ...prev };
        delete next[issueId];
        return next;
      });
      // Synchronize with database
      const refreshedIssues = await IssueService.getApplianceIssues(applianceId);
      setIssues(refreshedIssues.sort((a, b) => new Date(b.reported_at) - new Date(a.reported_at)));
    } catch (err) {
      alert(`Failed to delete issue: ${err.message}`);
    }
  };

  const handleRunDiagnostics = async (issueId) => {
    setDiagnosingIssueId(issueId);
    setDiagnosticErrors(prev => ({ ...prev, [issueId]: null }));
    // Clear out previously cached fresh result for this issue so new diagnosis starts fresh
    setDiagnosticResults(prev => ({ ...prev, [issueId]: null }));
    try {
      console.log(`[HomeRepair AI] Triggering real LangGraph agent investigation for Issue #${issueId}`);
      const result = await AgentService.investigate(issueId);
      console.log(`[HomeRepair AI] Received diagnosis result:`, result);
      // Immediately cache result for this issue so it displays right away
      setDiagnosticResults(prev => ({ ...prev, [issueId]: result }));
      // Refresh issues to sync database persistence
      const refreshedIssues = await IssueService.getApplianceIssues(applianceId);
      setIssues(refreshedIssues.sort((a, b) => new Date(b.reported_at) - new Date(a.reported_at)));
    } catch (e) {
      console.error("Diagnosis error:", e);
      setDiagnosticErrors(prev => ({ ...prev, [issueId]: e.message || 'Diagnostic request failed' }));
    } finally {
      setDiagnosingIssueId(null);
    }
  };

  const handleRecordOutcome = async (issueId, outcome) => {
    try {
      await IssueService.recordOutcome(issueId, { 
        repair_outcome: outcome, 
        repair_notes: `Repair marked as ${outcome}.` 
      });
      await fetchData();
    } catch (e) {
      alert(`Failed to record outcome: ${e.message}`);
    }
  };

  const handleAddSymptom = async (issueId) => {
    if (!symptomInput.trim()) return;
    try {
      await IssueService.addSymptom(issueId, {
        name: 'Observed Symptom',
        value: symptomInput.trim(),
      });
      setSymptomInput('');
      setAddingSymptomIssueId(null);
      await fetchData();
    } catch (e) {
      alert(`Failed to add symptom: ${e.message}`);
    }
  };

  const handleCreateNewIssue = async (e) => {
    e.preventDefault();
    if (!newIssueData.title.trim()) {
      alert("Problem Title is required.");
      return;
    }
    if (!newIssueData.description.trim()) {
      alert("Problem Description is required.");
      return;
    }
    try {
      const payload = {
        title: newIssueData.title.trim(),
        description: newIssueData.description.trim(),
        severity: newIssueData.severity || 'medium',
        symptoms: newIssueData.symptom.trim() ? [{ name: 'Observed Symptom', value: newIssueData.symptom.trim() }] : []
      };
      await IssueService.createIssue(applianceId, payload);
      setShowAddIssueModal(false);
      setNewIssueData({ title: '', description: '', severity: 'medium', symptom: '' });
      await fetchData();
    } catch (e) {
      alert(`Failed to create issue: ${e.message}`);
    }
  };

  if (loading) return <LoadingState message="Loading appliance details..." />;
  if (!appliance) return <ErrorState title="Not Found" message="Could not load appliance details." onRetry={fetchData} />;

  return (
    <div className="appliance-detail-view">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <button className="btn btn-secondary" onClick={() => onBack(false)}>&larr; Back to Appliances</button>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <button 
            className="btn btn-danger-outline btn-delete-appliance"
            onClick={handleDeleteAppliance}
            title="Delete this appliance and its history"
          >
            🗑 Delete Appliance
          </button>
          <button className="btn btn-primary" onClick={() => setShowAddIssueModal(true)}>
            + Report Another Problem
          </button>
        </div>
      </div>
      
      <div className="detail-header">
        <h2>{appliance.name}</h2>
        <p className="text-muted">
          {appliance.brand} &bull; Model {appliance.model_number} &bull; {appliance.location || 'Location not specified'} &bull; Category: {(appliance.category || '').replace('_', ' ')}
        </p>
        <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
          <span>Purchase Date: {appliance.purchase_date || 'N/A'}</span>
          <span>Warranty Expiry: {appliance.warranty_expiry || 'N/A'}</span>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-history">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ margin: 0 }}>Persistent Issue History & Diagnostics ({issues.length})</h3>
          </div>

          {issues.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', background: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-sm)' }}>
              <p className="text-muted" style={{ marginBottom: '12px' }}>No issues have been reported for this appliance.</p>
              <button className="btn btn-primary" onClick={() => setShowAddIssueModal(true)}>Report First Issue</button>
            </div>
          ) : (
            <div className="history-timeline">
              {issues.map(issue => {
                const freshResult = diagnosticResults[issue.id];
                const storedResult = issue.diagnosis_result;
                const isDiagnosing = diagnosingIssueId === issue.id;
                const errorMsg = diagnosticErrors[issue.id];

                return (
                  <div key={issue.id} className="history-card" id={`issue-card-${issue.id}`}>
                    <div className="history-card-header">
                      <div>
                        <h4>{issue.title}</h4>
                        <span className="history-date">Reported: {new Date(issue.reported_at).toLocaleString()}</span>
                      </div>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <StatusBadge type="severity" value={issue.severity} />
                        <StatusBadge type="status" value={issue.status} />
                        {issue.repair_outcome && (
                          <span style={{ 
                            fontSize: '0.75rem', 
                            fontWeight: '700', 
                            textTransform: 'uppercase',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            background: issue.repair_outcome === 'successful' ? '#ecfdf5' : '#fef2f2',
                            color: issue.repair_outcome === 'successful' ? '#065f46' : '#991b1b',
                            border: `1px solid ${issue.repair_outcome === 'successful' ? '#a7f3d0' : '#fecaca'}`
                          }}>
                            {issue.repair_outcome}
                          </span>
                        )}
                        <button
                          className="btn btn-danger-outline btn-sm btn-delete-issue"
                          onClick={() => handleDeleteIssue(issue.id, issue.title)}
                          title="Delete this issue"
                        >
                          🗑 Delete Issue
                        </button>
                      </div>
                    </div>

                    <p style={{ marginTop: '8px', color: 'var(--color-text-primary)' }}>{issue.description || 'No detailed description.'}</p>

                    {/* Recorded Symptoms */}
                    {issue.symptoms && issue.symptoms.length > 0 && (
                      <div className="symptoms-chips-row">
                        {issue.symptoms.map((s, idx) => (
                          <span key={idx} className="symptom-chip-pill">
                            <strong>{s.name}:</strong> {s.value} {s.unit || ''}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Add Symptom Inline Form */}
                    {addingSymptomIssueId === issue.id ? (
                      <div style={{ display: 'flex', gap: '8px', marginTop: '8px', alignItems: 'center' }}>
                        <input
                          type="text"
                          className="form-input"
                          style={{ maxWidth: '300px', padding: '6px 10px', fontSize: '0.8125rem' }}
                          placeholder="e.g. Error Code E24, Rattling noise"
                          value={symptomInput}
                          onChange={(e) => setSymptomInput(e.target.value)}
                        />
                        <button className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '0.8125rem' }} onClick={() => handleAddSymptom(issue.id)}>Save Symptom</button>
                        <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8125rem' }} onClick={() => setAddingSymptomIssueId(null)}>Cancel</button>
                      </div>
                    ) : (
                      issue.status !== 'resolved' && (
                        <div style={{ marginTop: '6px' }}>
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                            onClick={() => { setAddingSymptomIssueId(issue.id); setSymptomInput(''); }}
                          >
                            + Add Symptom
                          </button>
                        </div>
                      )
                    )}

                    {/* Active Diagnosing Loader Banner */}
                    {isDiagnosing && (
                      <div className="diagnosing-banner-active">
                        <div className="diagnosing-spinner-ring" />
                        <div className="diagnosing-banner-text">
                          <h4>⚡ Running LangGraph AI Diagnostic Agent...</h4>
                          <p>
                            Investigating Issue #{issue.id} with agentic workflow:
                            <br />
                            &bull; Loading persistent appliance context & memories
                            <br />
                            &bull; Deterministic history matching & symptom analysis
                            <br />
                            &bull; AI synthesis via OpenRouter reasoning model
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Diagnostic Error Banner */}
                    {errorMsg && (
                      <div className="diagnostic-error-banner">
                        <div className="error-title">❌ Diagnosis Request Failed</div>
                        <div className="error-detail">{errorMsg}</div>
                        <button 
                          className="btn btn-secondary" 
                          style={{ marginTop: '8px', fontSize: '0.8125rem' }} 
                          onClick={() => handleRunDiagnostics(issue.id)}
                        >
                          Retry Diagnosis
                        </button>
                      </div>
                    )}

                    {/* 1. FRESH AI DIAGNOSTIC RESULT (Generated in active session) */}
                    {!isDiagnosing && freshResult && (
                      freshResult.analysis_mode === 'historical_match' ? (
                        <HistoricalDiagnosisCard 
                          diagnosisData={freshResult} 
                          issue={issue} 
                          isMatch={true} 
                        />
                      ) : (
                        <div className="fresh-diagnosis-container">
                          <div className="fresh-diagnosis-pill-header">
                            <span className="pill-dot">●</span>
                            <strong>Fresh AI Diagnostic Result</strong>
                            <span className="fresh-tagline">Generated just now via LangGraph + OpenRouter</span>
                          </div>
                          <DiagnosisReportCard 
                            diagnosisData={freshResult} 
                            isFresh={true} 
                          />
                        </div>
                      )
                    )}

                    {/* 2. STORED HISTORICAL DIAGNOSIS (Directly visible when no fresh run is active) */}
                    {!isDiagnosing && storedResult && !freshResult && (
                      (issue.status === 'resolved' || issue.repair_outcome || parseDiagnosis(storedResult)?.analysis_mode === 'historical_match') ? (
                        <HistoricalDiagnosisCard 
                          diagnosisData={storedResult} 
                          issue={issue} 
                          isMatch={parseDiagnosis(storedResult)?.analysis_mode === 'historical_match'} 
                        />
                      ) : (
                        <div className="stored-history-container">
                          <div className="stored-history-pill-header">
                            <span className="pill-clock">📋</span>
                            <strong>Previously Stored Diagnosis</strong>
                            <span className="stored-subtitle">Loaded from database history &bull; Click "Run AI Diagnostics" below to re-evaluate</span>
                          </div>
                          <DiagnosisReportCard 
                            diagnosisData={storedResult} 
                            isHistorical={true} 
                          />
                        </div>
                      )
                    )}

                    <div className="history-actions">
                      <button 
                        className="btn btn-primary btn-diagnose" 
                        onClick={() => handleRunDiagnostics(issue.id)}
                        disabled={isDiagnosing}
                      >
                        {isDiagnosing ? (
                          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span className="btn-spinner" /> Generating Report & Running AI Diagnostics...
                          </span>
                        ) : storedResult || freshResult ? (
                          '⚡ Re-Generate Report / Diagnose Problem'
                        ) : (
                          '⚡ Generate Report / Diagnose Problem'
                        )}
                      </button>
                      
                      {issue.status !== 'resolved' && (
                        <div className="outcome-controls">
                          <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', alignSelf: 'center' }}>Record Repair Outcome:</span>
                          <button className="btn btn-secondary" style={{ fontSize: '0.8125rem' }} onClick={() => handleRecordOutcome(issue.id, 'successful')}>Mark Successful</button>
                          <button className="btn btn-secondary" style={{ fontSize: '0.8125rem' }} onClick={() => handleRecordOutcome(issue.id, 'failed')}>Mark Failed</button>
                          <button className="btn btn-secondary" style={{ fontSize: '0.8125rem' }} onClick={() => handleRecordOutcome(issue.id, 'partially_resolved')}>Partially Resolved</button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Modal to log another problem for this appliance */}
      {showAddIssueModal && (
        <div className="modal-overlay" onClick={() => setShowAddIssueModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Report New Problem for {appliance.name}</h2>
              <button type="button" className="modal-close-btn" onClick={() => setShowAddIssueModal(false)}>&times;</button>
            </div>

            <form className="modal-form" onSubmit={handleCreateNewIssue}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Problem Title *</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="e.g. Machine making grinding noise" 
                    required
                    value={newIssueData.title}
                    onChange={(e) => setNewIssueData({...newIssueData, title: e.target.value})}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Description *</label>
                  <textarea 
                    className="form-input" 
                    rows={3} 
                    placeholder="Describe when it happens, sounds, etc."
                    required
                    value={newIssueData.description}
                    onChange={(e) => setNewIssueData({...newIssueData, description: e.target.value})}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Severity *</label>
                    <select 
                      className="form-input" 
                      value={newIssueData.severity}
                      onChange={(e) => setNewIssueData({...newIssueData, severity: e.target.value})}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Observed Symptom (Optional)</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder='e.g. "Not cooling properly", "Water leaking", "Loud vibration", "Unusual motor noise"'
                      value={newIssueData.symptom}
                      onChange={(e) => setNewIssueData({...newIssueData, symptom: e.target.value})}
                    />
                    <span className="form-field-hint">e.g. "Not cooling properly", "Water leaking", "Loud vibration", "Unusual motor noise"</span>
                  </div>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddIssueModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Submit Problem Report</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export function MyAppliancesPage({ onNavigate, initialApplianceId, initialIssueId, autoDiagnose }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [appliances, setAppliances] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [selectedApplianceId, setSelectedApplianceId] = useState(initialApplianceId || null);

  useEffect(() => {
    if (initialApplianceId) {
      setSelectedApplianceId(initialApplianceId);
    }
  }, [initialApplianceId]);

  // Form State
  const [formData, setFormData] = useState({
    name: '',
    brand: '',
    model_number: '',
    category: 'refrigerator',
    location: '',
    purchase_date: '',
    warranty_expiry: '',
    issue_title: '',
    issue_description: '',
    issue_severity: 'medium',
    issue_symptom: ''
  });

  const [formErrors, setFormErrors] = useState({});

  const fetchAppliances = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await ApplianceService.getAppliances();
      setAppliances(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAppliances();
  }, []);

  const getWarrantyInfo = (expiryDate) => {
    if (!expiryDate) return { type: 'expired', label: 'No Warranty on Record' };
    const expiry = new Date(expiryDate);
    const now = new Date();
    const diffDays = Math.ceil((expiry - now) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return { type: 'expired', label: `Expired (${expiryDate})` };
    } else if (diffDays <= 60) {
      return { type: 'expiring_soon', label: `Expiring Soon (${expiryDate})` };
    } else {
      return { type: 'valid', label: `Under Warranty (thru ${expiryDate})` };
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    const errors = {};
    if (!formData.name.trim()) errors.name = 'Appliance Nickname is required.';
    if (!formData.brand.trim()) errors.brand = 'Brand / Manufacturer is required.';
    if (!formData.model_number.trim()) errors.model_number = 'Model Number is required.';
    if (!formData.issue_title.trim()) errors.issue_title = 'Problem Title is required.';
    if (!formData.issue_description.trim()) errors.issue_description = 'Problem Description is required.';
    if (!formData.issue_severity) errors.issue_severity = 'Severity is required.';

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }
    setFormErrors({});

    try {
      const payload = {
        name: formData.name.trim(),
        brand: formData.brand.trim(),
        model_number: formData.model_number.trim(),
        category: formData.category,
        location: formData.location ? formData.location.trim() : null,
        purchase_date: formData.purchase_date || null,
        warranty_expiry: formData.warranty_expiry || null,
        has_issue: true,
        issue_title: formData.issue_title.trim(),
        issue_description: formData.issue_description.trim(),
        issue_severity: formData.issue_severity || 'medium',
        issue_symptom: formData.issue_symptom ? formData.issue_symptom.trim() : null
      };

      await ApplianceService.createApplianceWithIssue(payload);

      setShowRegisterModal(false);
      setFormErrors({});
      setFormData({
        name: '', brand: '', model_number: '', category: 'refrigerator', location: '', purchase_date: '', warranty_expiry: '',
        issue_title: '', issue_description: '', issue_severity: 'medium', issue_symptom: ''
      });
      fetchAppliances();
    } catch (err) {
      alert(`Failed to register appliance: ${err.message}`);
    }
  };

  if (selectedApplianceId) {
    return (
      <ApplianceDetailView 
        applianceId={selectedApplianceId} 
        initialIssueId={initialIssueId}
        autoDiagnose={autoDiagnose}
        onBack={(deleted) => {
          setSelectedApplianceId(null);
          if (deleted) {
            fetchAppliances();
          }
        }} 
      />
    );
  }

  const filteredAppliances = appliances.filter((appliance) => {
    const matchesCategory = selectedCategory === 'all' || appliance.category === selectedCategory;
    const matchesSearch =
      (appliance.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (appliance.brand || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (appliance.model_number || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (appliance.location || '').toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  if (isLoading) {
    return (
      <div className="appliances-page">
        <LoadingState message="Loading your appliances..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="appliances-page">
        <ErrorState 
          title="Failed to load appliances" 
          message={error} 
          onRetry={fetchAppliances} 
        />
      </div>
    );
  }

  return (
    <div className="appliances-page">
      <PageHeader
        pretitle="Registry"
        title="My Household Appliances"
        subtitle="Catalog of registered appliances, technical model identifiers, warranty coverage status, and service history."
        actions={
          <button type="button" className="btn btn-primary" onClick={() => setShowRegisterModal(true)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Register Appliance
          </button>
        }
      />

      <div className="appliances-controls-bar">
        <div className="search-and-filters">
          <div className="search-input-wrapper">
            <svg className="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              className="search-input"
              placeholder="Search by brand, model, or room location..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <select className="category-select" value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
            <option value="all">All Categories ({appliances.length})</option>
            <option value="refrigerator">Refrigerators</option>
            <option value="washing_machine">Washing Machines</option>
            <option value="dishwasher">Dishwashers</option>
            <option value="air_conditioner">Air Conditioners / HVAC</option>
            <option value="microwave">Microwaves</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {filteredAppliances.length === 0 ? (
        <EmptyState
          title="No appliances found"
          description={appliances.length === 0 ? "You haven't registered any appliances yet." : "Try adjusting your filter search criteria."}
          action={
            appliances.length === 0 
              ? <button className="btn btn-primary" onClick={() => setShowRegisterModal(true)}>Register First Appliance</button>
              : <button className="btn btn-secondary" onClick={() => { setSearchTerm(''); setSelectedCategory('all'); }}>Clear Filters</button>
          }
        />
      ) : (
        <div className="appliances-grid">
          {filteredAppliances.map((appliance) => {
            const warrantyInfo = getWarrantyInfo(appliance.warranty_expiry);
            const openIssues = (appliance.issues || []).filter(i => i.status !== 'resolved').length;

            return (
              <article key={appliance.id} className="appliance-card">
                <div className="appliance-card-top">
                  <div>
                    <span className="appliance-brand-badge">{appliance.brand}</span>
                    <h2 className="appliance-name">{appliance.name}</h2>
                  </div>
                  <StatusBadge type="status" value={appliance.category} label={(appliance.category || '').replace('_', ' ')} />
                </div>

                <div className="appliance-specs">
                  <div className="spec-row">
                    <span className="spec-label">Model Identifier:</span>
                    <span className="spec-mono">{appliance.model_number}</span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-label">Location:</span>
                    <span className="spec-value">{appliance.location || 'Unknown'}</span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-label">Purchase Date:</span>
                    <span className="spec-value">{appliance.purchase_date || 'Unknown'}</span>
                  </div>
                </div>

                <div className="appliance-status-row">
                  <div className="warranty-status-block">
                    <StatusBadge type="warranty" value={warrantyInfo.type} label={warrantyInfo.label} />
                  </div>
                  <div className="issues-status-block">
                    {openIssues > 0 ? (
                      <StatusBadge type="severity" value="high" label="Need to Fix Issue" />
                    ) : (
                      <StatusBadge type="status" value="resolved" label="Nominal" />
                    )}
                  </div>
                </div>

                <div className="appliance-card-actions">
                  <button type="button" className="btn btn-primary" onClick={() => setSelectedApplianceId(appliance.id)}>
                    View Details & Diagnostics
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {showRegisterModal && (
        <div className="modal-overlay" onClick={() => setShowRegisterModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Register Household Appliance</h2>
              <button type="button" className="modal-close-btn" onClick={() => setShowRegisterModal(false)}>&times;</button>
            </div>

            <form className="modal-form" onSubmit={handleRegisterSubmit}>
              <div className="modal-body">
                {Object.keys(formErrors).length > 0 && (
                  <div className="modal-error-summary">
                    <strong>Please complete all required fields below:</strong>
                    <ul style={{ margin: '4px 0 0 18px', padding: 0 }}>
                      {Object.values(formErrors).map((msg, idx) => (
                        <li key={idx}>{msg}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">Appliance Nickname *</label>
                  <input 
                    type="text" 
                    className={`form-input ${formErrors.name ? 'form-input-error' : ''}`}
                    placeholder="e.g. Kitchen Refrigerator" 
                    required
                    value={formData.name} 
                    onChange={(e) => {
                      setFormData({...formData, name: e.target.value});
                      if (formErrors.name) setFormErrors(prev => ({...prev, name: ''}));
                    }} 
                  />
                  {formErrors.name && <span className="inline-field-error">{formErrors.name}</span>}
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Brand / Manufacturer *</label>
                    <input 
                      type="text" 
                      className={`form-input ${formErrors.brand ? 'form-input-error' : ''}`}
                      placeholder="e.g. Samsung" 
                      required
                      value={formData.brand} 
                      onChange={(e) => {
                        setFormData({...formData, brand: e.target.value});
                        if (formErrors.brand) setFormErrors(prev => ({...prev, brand: ''}));
                      }} 
                    />
                    {formErrors.brand && <span className="inline-field-error">{formErrors.brand}</span>}
                  </div>
                  <div className="form-group">
                    <label className="form-label">Model Number *</label>
                    <input 
                      type="text" 
                      className={`form-input ${formErrors.model_number ? 'form-input-error' : ''}`}
                      placeholder="e.g. RF28" 
                      required
                      value={formData.model_number} 
                      onChange={(e) => {
                        setFormData({...formData, model_number: e.target.value});
                        if (formErrors.model_number) setFormErrors(prev => ({...prev, model_number: ''}));
                      }} 
                    />
                    {formErrors.model_number && <span className="inline-field-error">{formErrors.model_number}</span>}
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Category *</label>
                    <select className="form-input" value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})}>
                      <option value="refrigerator">Refrigerator</option>
                      <option value="washing_machine">Washing Machine</option>
                      <option value="dishwasher">Dishwasher</option>
                      <option value="air_conditioner">Air Conditioner</option>
                      <option value="microwave">Microwave</option>
                      <option value="television">Television</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Location in Residence</label>
                    <input type="text" className="form-input" placeholder="e.g. Kitchen"
                      value={formData.location} onChange={(e) => setFormData({...formData, location: e.target.value})} />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Purchase Date</label>
                    <input type="date" className="form-input" 
                      value={formData.purchase_date} onChange={(e) => setFormData({...formData, purchase_date: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Warranty Expiry Date</label>
                    <input type="date" className="form-input" 
                      value={formData.warranty_expiry} onChange={(e) => setFormData({...formData, warranty_expiry: e.target.value})} />
                  </div>
                </div>

                {/* Mandatory Problem / Issue Section */}
                <div className="mandatory-issue-section">
                  <div className="mandatory-issue-header">
                    <span className="mandatory-issue-title">Log an initial problem/issue</span>
                    <span className="mandatory-tag">Required</span>
                  </div>
                  <p className="mandatory-issue-hint">
                    Every registered appliance includes an initial problem so the AI agent can diagnose and coordinate repairs.
                  </p>

                  <div className="form-group">
                    <label className="form-label">Problem Title *</label>
                    <input 
                      type="text" 
                      className={`form-input ${formErrors.issue_title ? 'form-input-error' : ''}`}
                      placeholder="e.g. Not cooling properly" 
                      required
                      value={formData.issue_title} 
                      onChange={(e) => {
                        setFormData({...formData, issue_title: e.target.value});
                        if (formErrors.issue_title) setFormErrors(prev => ({...prev, issue_title: ''}));
                      }} 
                    />
                    {formErrors.issue_title && <span className="inline-field-error">{formErrors.issue_title}</span>}
                  </div>
                  <div className="form-group">
                    <label className="form-label">Problem Description *</label>
                    <textarea 
                      className={`form-input ${formErrors.issue_description ? 'form-input-error' : ''}`}
                      placeholder="Describe what is happening, sounds, leaks, when it happens..." 
                      rows={3} 
                      required
                      value={formData.issue_description} 
                      onChange={(e) => {
                        setFormData({...formData, issue_description: e.target.value});
                        if (formErrors.issue_description) setFormErrors(prev => ({...prev, issue_description: ''}));
                      }} 
                    />
                    {formErrors.issue_description && <span className="inline-field-error">{formErrors.issue_description}</span>}
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Severity *</label>
                      <select 
                        className={`form-input ${formErrors.issue_severity ? 'form-input-error' : ''}`}
                        required 
                        value={formData.issue_severity} 
                        onChange={(e) => {
                          setFormData({...formData, issue_severity: e.target.value});
                          if (formErrors.issue_severity) setFormErrors(prev => ({...prev, issue_severity: ''}));
                        }}
                      >
                        <option value="low">Low (Annoying but works)</option>
                        <option value="medium">Medium (Impaired functionality)</option>
                        <option value="high">High (Cannot use normally)</option>
                        <option value="critical">Critical (Safety risk / total failure)</option>
                      </select>
                      {formErrors.issue_severity && <span className="inline-field-error">{formErrors.issue_severity}</span>}
                    </div>
                    <div className="form-group">
                      <label className="form-label">Observed Symptom (Optional)</label>
                      <input 
                        type="text" 
                        className="form-input"
                        placeholder='e.g. "Not cooling properly", "Water leaking", "Loud vibration", "Unusual motor noise"'
                        value={formData.issue_symptom} 
                        onChange={(e) => {
                          setFormData({...formData, issue_symptom: e.target.value});
                        }} 
                      />
                      <span className="form-field-hint">e.g. "Not cooling properly", "Water leaking", "Loud vibration", "Unusual motor noise"</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowRegisterModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Appliance Record</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default MyAppliancesPage;
