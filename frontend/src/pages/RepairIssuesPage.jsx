import React, { useState, useEffect } from 'react';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { IssueService, ApplianceService } from '../services/api';
import './RepairIssuesPage.css';

export function RepairIssuesPage({ onNavigate, filterApplianceId }) {
  const [activeFilter, setActiveFilter] = useState('all');
  const [issues, setIssues] = useState([]);
  const [appliances, setAppliances] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showReportModal, setShowReportModal] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    appliance_id: filterApplianceId || '',
    title: '',
    description: '',
    severity: 'medium',
    initial_symptom: ''
  });

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // If we have an appliance filter, just fetch its issues, otherwise we'd ideally fetch all issues.
      // But the API currently only has GET /appliances/{id}/issues. 
      // So if no filterApplianceId, we fetch all appliances and then all their issues.
      let fetchedAppliances = await ApplianceService.getAppliances();
      setAppliances(fetchedAppliances);

      let allIssues = [];
      if (filterApplianceId) {
        allIssues = await IssueService.getApplianceIssues(filterApplianceId);
      } else {
        // Fetch issues for all active appliances
        const issuePromises = fetchedAppliances.map(app => 
          IssueService.getApplianceIssues(app.id).catch(() => []) // ignore errors for single appliances
        );
        const issuesArrays = await Promise.all(issuePromises);
        allIssues = issuesArrays.flat();
      }

      // Attach appliance info to issues for display
      const issuesWithApplianceInfo = allIssues.map(issue => {
        const app = fetchedAppliances.find(a => a.id === issue.appliance_id);
        return {
          ...issue,
          appliance_name: app ? app.name : 'Unknown Appliance',
          appliance_brand: app ? app.brand : '',
          appliance_model: app ? app.model_number : '',
          appliance_location: app ? app.location : ''
        };
      });

      // Sort by newest first
      issuesWithApplianceInfo.sort((a, b) => new Date(b.reported_at) - new Date(a.reported_at));
      
      setIssues(issuesWithApplianceInfo);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filterApplianceId]);

  const handleReportSubmit = async (e) => {
    e.preventDefault();
    if (!formData.appliance_id) {
      alert("Please select an appliance.");
      return;
    }
    
    try {
      const payload = {
        title: formData.title,
        description: formData.description,
        severity: formData.severity,
      };
      
      const newIssue = await IssueService.createIssue(formData.appliance_id, payload);
      
      // If there is an initial symptom, we might need to create it using a symptom service, 
      // but for now the user prompt just mentioned "optional initial symptom".
      // We can pass it in the description or if the backend supports nested creation.
      
      setShowReportModal(false);
      setFormData({
        appliance_id: filterApplianceId || '',
        title: '',
        description: '',
        severity: 'medium',
        initial_symptom: ''
      });
      fetchData();
    } catch (err) {
      alert(`Failed to report issue: ${err.message}`);
    }
  };

  const filteredIssues = issues.filter((issue) => {
    const matchesStatus = activeFilter === 'all' || issue.status === activeFilter;
    return matchesStatus;
  });

  if (isLoading) {
    return (
      <div className="repair-issues-page">
        <LoadingState message="Loading reported issues..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="repair-issues-page">
        <ErrorState title="Failed to load issues" message={error} onRetry={fetchData} />
      </div>
    );
  }

  return (
    <div className="repair-issues-page">
      <PageHeader
        pretitle="Troubleshooting"
        title="Appliance Repair Issues"
        subtitle="Reported malfunctions, recorded symptoms, diagnostic investigation progress, and corrective actions."
        actions={
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setShowReportModal(true)}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Report New Issue
          </button>
        }
      />

      {/* Filter Tabs */}
      <div className="issues-filter-tabs">
        <button type="button" className={`tab-btn ${activeFilter === 'all' ? 'active' : ''}`} onClick={() => setActiveFilter('all')}>
          All Issues ({issues.length})
        </button>
        <button type="button" className={`tab-btn ${activeFilter === 'open' ? 'active' : ''}`} onClick={() => setActiveFilter('open')}>
          Open
        </button>
        <button type="button" className={`tab-btn ${activeFilter === 'investigating' ? 'active' : ''}`} onClick={() => setActiveFilter('investigating')}>
          Investigating
        </button>
        <button type="button" className={`tab-btn ${activeFilter === 'repair_recommended' ? 'active' : ''}`} onClick={() => setActiveFilter('repair_recommended')}>
          Repair Recommended
        </button>
        <button type="button" className={`tab-btn ${activeFilter === 'resolved' ? 'active' : ''}`} onClick={() => setActiveFilter('resolved')}>
          Resolved
        </button>
      </div>

      {/* Issues Listing */}
      {filteredIssues.length === 0 ? (
        <EmptyState
          title="No issues found"
          description={issues.length === 0 ? "There are currently no reported problems." : "There are no problems matching the selected status filter."}
          action={
            issues.length === 0 
              ? <button className="btn btn-primary" onClick={() => setShowReportModal(true)}>Report First Issue</button>
              : <button className="btn btn-secondary" onClick={() => setActiveFilter('all')}>Show All Issues</button>
          }
        />
      ) : (
        <div className="issues-list">
          {filteredIssues.map((issue) => (
            <article key={issue.id} className="issue-card">
              <div className="issue-card-header">
                <div>
                  <div className="issue-meta-appliance">
                    {issue.appliance_brand} {issue.appliance_name} &bull; Model {issue.appliance_model} &bull; {issue.appliance_location || 'Unknown location'}
                  </div>
                  <h2 className="issue-title">{issue.title}</h2>
                </div>
                <div className="issue-badges">
                  <StatusBadge type="severity" value={issue.severity} />
                  <StatusBadge type="status" value={issue.status} />
                </div>
              </div>

              <p className="issue-description">{issue.description || 'No description provided.'}</p>

              {/* Structured Symptoms Chips */}
              {issue.symptoms && issue.symptoms.length > 0 && (
                <div className="issue-symptoms-panel">
                  <div className="symptoms-title">Recorded Diagnostic Symptoms ({issue.symptoms.length})</div>
                  <div className="symptoms-chips">
                    {issue.symptoms.map((s) => (
                      <span key={s.id} className="symptom-chip">
                        <span className="symptom-chip-name">{s.name}:</span>
                        <span className="symptom-chip-value">
                          {s.value} {s.unit || ''}
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="issue-card-footer">
                <span className="issue-reported-time">
                  Reported: {new Date(issue.reported_at).toLocaleDateString()} at {new Date(issue.reported_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>

                <div className="issue-actions">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => onNavigate('appliances', { issueId: issue.id, applianceId: issue.appliance_id })}
                  >
                    View Details & Diagnostics &rarr;
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Report New Issue Modal */}
      {showReportModal && (
        <div className="modal-overlay" onClick={() => setShowReportModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Report Appliance Issue</h2>
              <button type="button" className="modal-close-btn" onClick={() => setShowReportModal(false)}>&times;</button>
            </div>

            <form className="modal-form" onSubmit={handleReportSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Select Appliance</label>
                  <select 
                    className="form-input" 
                    required
                    value={formData.appliance_id} 
                    onChange={(e) => setFormData({...formData, appliance_id: e.target.value})}
                    disabled={!!filterApplianceId}
                  >
                    <option value="">-- Choose Appliance --</option>
                    {appliances.map(app => (
                      <option key={app.id} value={app.id}>{app.name} ({app.brand} {app.model_number})</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Issue Title</label>
                  <input type="text" className="form-input" placeholder="e.g. Fridge not cooling" required
                    value={formData.title} onChange={(e) => setFormData({...formData, title: e.target.value})} />
                </div>

                <div className="form-group">
                  <label className="form-label">Description (Optional)</label>
                  <textarea 
                    className="form-input" 
                    placeholder="Provide more details about the problem..."
                    rows="3"
                    value={formData.description} 
                    onChange={(e) => setFormData({...formData, description: e.target.value})} 
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Severity</label>
                    <select className="form-input" value={formData.severity} onChange={(e) => setFormData({...formData, severity: e.target.value})}>
                      <option value="low">Low - Minor annoyance</option>
                      <option value="medium">Medium - Needs attention soon</option>
                      <option value="high">High - Functionality impacted</option>
                      <option value="critical">Critical - Unusable / Safety Risk</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Initial Symptom (Optional)</label>
                    <input type="text" className="form-input" placeholder="e.g. Strange noise"
                      value={formData.initial_symptom} onChange={(e) => setFormData({...formData, initial_symptom: e.target.value})} />
                  </div>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowReportModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Submit Report</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default RepairIssuesPage;
