import React from 'react';
import { useSelector } from 'react-redux';

/**
 * CapaRecommendation
 *
 * Advisory UI component providing structured Corrective and Preventive Action (CAPA)
 * recommendations based on complaint details, risk assessment, and severity.
 *
 * Fully deterministic & lightweight: 0 extra LLM calls, 0 database migrations.
 * Automatically restores upon reopening saved complaints via persisted risk/type fields.
 */

const ClipboardIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2.2" aria-hidden="true">
    <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/>
    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
    <path d="M9 12h6M9 16h6"/>
  </svg>
);

const CheckSquareIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <polyline points="9 11 12 14 22 4"/>
    <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
  </svg>
);

const RefreshIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <path d="M23 4v6h-6"/>
    <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
  </svg>
);

const getCapaRecommendations = (complaintType, severity, batchNumber) => {
  const typeLower = (complaintType || '').toLowerCase();
  const batchStr = batchNumber ? ` (Batch #${batchNumber})` : '';

  let corrective = [];
  let preventive = [];

  if (typeLower.includes('packaging')) {
    corrective = [
      `Quarantine affected packaging lot${batchStr} immediately.`,
      `Inspect seal integrity and blister foil parameters on packaging line.`,
      `Perform 100% visual inspection on remaining stock of affected batch.`
    ];
    preventive = [
      `Recalibrate sealing temperature and pressure sensors on packaging equipment.`,
      `Issue vendor non-conformance report to primary packaging foil supplier.`,
      `Review SOP-PKG-204 for routine seal strength testing during production runs.`
    ];
  } else if (typeLower.includes('contamination') || typeLower.includes('foreign') || typeLower.includes('particle')) {
    corrective = [
      `Place affected product batch${batchStr} on immediate quality hold.`,
      `Initiate analytical microscopy / FTIR analysis on foreign matter samples.`,
      `Review HVAC environmental monitoring logs for the filling area.`
    ];
    preventive = [
      `Conduct comprehensive sanitization and HEPA filter integrity check in processing suite.`,
      `Enhance operator gowning audit frequency and cleanroom entrance protocols.`,
      `Update SOP-CLEAN-108 with mandatory pre-use line clearance inspection steps.`
    ];
  } else if (typeLower.includes('mislabel') || typeLower.includes('label')) {
    corrective = [
      `Quarantine all labeled units from affected run${batchStr}.`,
      `Verify label roll reconciliation against master packaging batch record.`,
      `Perform barcode scanner verification across secondary packaging inventory.`
    ];
    preventive = [
      `Implement automated vision inspection for label verification on the line.`,
      `Audit label printing vendor for artwork version control and roll segregation.`,
      `Update SOP-LBL-302 to require double-signoff before releasing label rolls to line.`
    ];
  } else if (typeLower.includes('adverse') || typeLower.includes('efficacy') || typeLower.includes('potency')) {
    corrective = [
      `Notify Pharmacovigilance and Quality Management within 24 hours.`,
      `Initiate retain sample potency assay and dissolution testing${batchStr}.`,
      `Perform stability testing review for the affected commercial lot.`
    ];
    preventive = [
      `Review API raw material Certificates of Analysis across recent manufacturing lots.`,
      `Re-validate blender uniformity parameters and compaction force limits.`,
      `Schedule annual product quality review (APQR) focus audit on dissolution performance.`
    ];
  } else {
    // Default Quality Defect / General Complaint CAPA
    corrective = [
      `Quarantine remaining inventory of reported batch${batchStr} pending investigation.`,
      `Inspect retain samples from the manufactured lot for similar defects.`,
      `Log formal QA deviation report and assign lead Quality Investigator.`
    ];
    preventive = [
      `Conduct root-cause analysis (5-Whys / Fishbone) to identify underlying cause.`,
      `Review manufacturing batch record execution and in-process testing logs.`,
      `Update relevant Quality Management System SOPs if systemic defect is confirmed.`
    ];
  }

  return { corrective, preventive };
};

export default function CapaRecommendation() {
  const { severity, riskLevel } = useSelector((s) => s.risk);
  const { analysisResult, selectedComplaint } = useSelector((s) => s.complaints);

  // Derive source complaint fields from analysisResult or selectedComplaint
  const complaintData = analysisResult?.complaint_data || selectedComplaint || {};
  const currentSeverity = severity || complaintData.severity || selectedComplaint?.severity || null;
  const complaintType = complaintData.complaint_type || selectedComplaint?.complaint_type || null;
  const batchNumber = complaintData.batch_number || selectedComplaint?.batch_number || null;

  const hasData = Boolean(currentSeverity || complaintType || analysisResult || selectedComplaint);

  if (!hasData) {
    return null;
  }

  const priorityLevel = (currentSeverity || 'Medium').toUpperCase();
  const priorityClass =
    priorityLevel === 'CRITICAL' ? 'priority-critical' :
    priorityLevel === 'HIGH' ? 'priority-high' :
    priorityLevel === 'MEDIUM' ? 'priority-med' : 'priority-low';

  const { corrective, preventive } = getCapaRecommendations(complaintType, currentSeverity, batchNumber);

  return (
    <div className="capa-card" role="region" aria-label="CAPA Recommendation">
      <div className="capa-card-header">
        <span className="capa-card-title">
          <ClipboardIcon />
          CAPA Recommendation
        </span>
        <span className={`capa-priority-badge ${priorityClass}`}>
          Priority: {priorityLevel}
        </span>
      </div>

      <p className="capa-card-subtitle">
        Recommended Corrective and Preventive Actions based on complaint classification and severity.
      </p>

      <div className="capa-grid">
        {/* Corrective Action Section */}
        <div className="capa-section">
          <div className="capa-section-title">
            <CheckSquareIcon />
            Immediate Corrective Action (Containment)
          </div>
          <ul className="capa-action-list">
            {corrective.map((item, idx) => (
              <li key={idx} className="capa-action-item">
                <span className="capa-bullet corrective-bullet">•</span>
                {item}
              </li>
            ))}
          </ul>
        </div>

        {/* Preventive Action Section */}
        <div className="capa-section">
          <div className="capa-section-title">
            <RefreshIcon />
            Preventive Action (Systemic Prevention)
          </div>
          <ul className="capa-action-list">
            {preventive.map((item, idx) => (
              <li key={idx} className="capa-action-item">
                <span className="capa-bullet preventive-bullet">•</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

