const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api';

async function handleResponse(response) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `API Error: ${response.statusText}`);
  }
  return response.json();
}

export const ApplianceService = {
  getAppliances: async () => {
    const response = await fetch(`${API_BASE}/appliances`);
    return handleResponse(response);
  },

  getAppliance: async (id) => {
    const response = await fetch(`${API_BASE}/appliances/${id}`);
    return handleResponse(response);
  },

  createAppliance: async (applianceData) => {
    const response = await fetch(`${API_BASE}/appliances`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(applianceData),
    });
    return handleResponse(response);
  },

  createApplianceWithIssue: async (payload) => {
    const response = await fetch(`${API_BASE}/appliances/with-issue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse(response);
  },

  deleteAppliance: async (id) => {
    const response = await fetch(`${API_BASE}/appliances/${id}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};

export const IssueService = {
  getApplianceIssues: async (applianceId) => {
    const response = await fetch(`${API_BASE}/appliances/${applianceId}/issues`);
    return handleResponse(response);
  },

  getIssue: async (issueId) => {
    const response = await fetch(`${API_BASE}/issues/${issueId}`);
    return handleResponse(response);
  },

  createIssue: async (applianceId, issueData) => {
    const response = await fetch(`${API_BASE}/appliances/${applianceId}/issues`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(issueData),
    });
    return handleResponse(response);
  },

  updateIssue: async (issueId, updateData) => {
    const response = await fetch(`${API_BASE}/issues/${issueId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData),
    });
    return handleResponse(response);
  },

  recordOutcome: async (issueId, outcomeData) => {
    const response = await fetch(`${API_BASE}/issues/${issueId}/outcome`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(outcomeData),
    });
    return handleResponse(response);
  },

  storeDiagnosis: async (issueId, diagnosisJson) => {
    const params = new URLSearchParams({ diagnosis_json: diagnosisJson });
    const response = await fetch(`${API_BASE}/issues/${issueId}/diagnosis?${params}`, {
      method: 'PATCH',
    });
    return handleResponse(response);
  },

  addSymptom: async (issueId, symptomData) => {
    const response = await fetch(`${API_BASE}/issues/${issueId}/symptoms`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(symptomData),
    });
    return handleResponse(response);
  },

  deleteIssue: async (issueId) => {
    const response = await fetch(`${API_BASE}/issues/${issueId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `API Error: ${response.statusText}`);
    }
    return true;
  },
};

export const RepairService = {
  getApplianceRepairs: async (applianceId) => {
    const response = await fetch(`${API_BASE}/appliances/${applianceId}/repairs`);
    return handleResponse(response);
  },
};

export const AgentService = {
  investigate: async (issueId) => {
    const response = await fetch(`${API_BASE}/agent/investigate/${issueId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({}),
    });
    return handleResponse(response);
  },
};
