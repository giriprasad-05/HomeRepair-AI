import React, { useState } from 'react';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import { MOCK_APPLIANCES } from '../utils/mockData';
import './MyAppliancesPage.css';

export function MyAppliancesPage({ onNavigate }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showRegisterModal, setShowRegisterModal] = useState(false);

  // Helper to determine warranty status
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

  const filteredAppliances = MOCK_APPLIANCES.filter((appliance) => {
    const matchesCategory =
      selectedCategory === 'all' || appliance.category === selectedCategory;
    const matchesSearch =
      appliance.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      appliance.brand.toLowerCase().includes(searchTerm.toLowerCase()) ||
      appliance.model_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      appliance.location.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="appliances-page">
      <PageHeader
        pretitle="Registry"
        title="My Household Appliances"
        subtitle="Catalog of registered appliances, technical model identifiers, warranty coverage status, and service history."
        actions={
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setShowRegisterModal(true)}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Register Appliance
          </button>
        }
      />

      {/* Filter and Search Bar */}
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

          <select
            className="category-select"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="all">All Categories ({MOCK_APPLIANCES.length})</option>
            <option value="refrigerator">Refrigerators</option>
            <option value="washing_machine">Washing Machines</option>
            <option value="dishwasher">Dishwashers</option>
            <option value="air_conditioner">Air Conditioners / HVAC</option>
            <option value="microwave">Microwaves</option>
          </select>
        </div>
      </div>

      {/* Appliance Cards Listing */}
      {filteredAppliances.length === 0 ? (
        <EmptyState
          title="No appliances found"
          description="Try adjusting your filter search criteria or register a new appliance."
          action={
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setSearchTerm('');
                setSelectedCategory('all');
              }}
            >
              Clear Filters
            </button>
          }
        />
      ) : (
        <div className="appliances-grid">
          {filteredAppliances.map((appliance) => {
            const warrantyInfo = getWarrantyInfo(appliance.warranty_expiry);

            return (
              <article key={appliance.id} className="appliance-card">
                <div className="appliance-card-top">
                  <div>
                    <span className="appliance-brand-badge">{appliance.brand}</span>
                    <h2 className="appliance-name">{appliance.name}</h2>
                  </div>
                  <StatusBadge
                    type="status"
                    value={appliance.category}
                    label={appliance.category.replace('_', ' ')}
                  />
                </div>

                <div className="appliance-specs">
                  <div className="spec-row">
                    <span className="spec-label">Model Identifier:</span>
                    <span className="spec-mono">{appliance.model_number}</span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-label">Location:</span>
                    <span className="spec-value">{appliance.location}</span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-label">Purchase Date:</span>
                    <span className="spec-value">{appliance.purchase_date || 'Unknown'}</span>
                  </div>
                </div>

                <div className="appliance-status-row">
                  <div className="warranty-status-block">
                    <StatusBadge
                      type="warranty"
                      value={warrantyInfo.type}
                      label={warrantyInfo.label}
                    />
                  </div>
                  <div className="issues-status-block">
                    {appliance.open_issue_count > 0 ? (
                      <StatusBadge
                        type="severity"
                        value="high"
                        label={`${appliance.open_issue_count} Active Issue`}
                      />
                    ) : (
                      <StatusBadge
                        type="status"
                        value="resolved"
                        label="No Open Issues"
                      />
                    )}
                  </div>
                </div>

                <div className="appliance-card-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() =>
                      onNavigate('issues', { applianceId: appliance.id })
                    }
                  >
                    View History
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() =>
                      onNavigate('investigation', { applianceId: appliance.id })
                    }
                  >
                    Diagnose
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {/* Register Appliance Modal Placeholder */}
      {showRegisterModal && (
        <div className="modal-overlay" onClick={() => setShowRegisterModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Register Household Appliance</h2>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setShowRegisterModal(false)}
              >
                &times;
              </button>
            </div>

            <form
              className="modal-form"
              onSubmit={(e) => {
                e.preventDefault();
                setShowRegisterModal(false);
              }}
            >
              <div className="form-group">
                <label className="form-label">Appliance Nickname</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Kitchen Refrigerator, Guest Room AC"
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Brand / Manufacturer</label>
                  <input type="text" className="form-input" placeholder="e.g. Samsung, Whirlpool" required />
                </div>
                <div className="form-group">
                  <label className="form-label">Model Number</label>
                  <input type="text" className="form-input" placeholder="e.g. RF28R7351SR" required />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select className="form-input" defaultValue="refrigerator">
                    <option value="refrigerator">Refrigerator</option>
                    <option value="washing_machine">Washing Machine</option>
                    <option value="dishwasher">Dishwasher</option>
                    <option value="air_conditioner">Air Conditioner</option>
                    <option value="microwave">Microwave</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Location in Residence</label>
                  <input type="text" className="form-input" placeholder="e.g. Kitchen, Laundry Room" />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Purchase Date</label>
                  <input type="date" className="form-input" />
                </div>
                <div className="form-group">
                  <label className="form-label">Warranty Expiry Date</label>
                  <input type="date" className="form-input" />
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowRegisterModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Appliance Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default MyAppliancesPage;
