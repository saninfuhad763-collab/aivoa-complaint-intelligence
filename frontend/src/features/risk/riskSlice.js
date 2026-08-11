import { createSlice } from '@reduxjs/toolkit';
import { analyzeComplaint, analyzePdfComplaint } from '../complaints/complaintSlice.js';

const initialState = {
  severity: null,
  riskLevel: null,
  initialAssessment: null,
  suggestedAction: null,
  confidence: null,
  missingFields: [],
};

const riskSlice = createSlice({
  name: 'risk',
  initialState,
  reducers: {
    setRiskAssessment: (state, action) => {
      const {
        severity,
        riskLevel,
        initialAssessment,
        suggestedAction,
        confidence,
        missingFields,
      } = action.payload || {};
      
      state.severity = severity ?? null;
      state.riskLevel = riskLevel ?? null;
      state.initialAssessment = initialAssessment ?? null;
      state.suggestedAction = suggestedAction ?? null;
      state.confidence = confidence ?? null;
      state.missingFields = missingFields || [];
    },
    updateRiskField: (state, action) => {
      const { field, value } = action.payload || {};
      if (field in state) {
        state[field] = value;
      }
    },
    clearRiskAssessment: () => initialState,
  },
  extraReducers: (builder) => {
    const updateRiskState = (state, action) => {
      const payload = action.payload || {};
      state.severity = payload.severity ?? null;
      state.riskLevel = payload.risk_level ?? null;
      state.initialAssessment = payload.initial_risk_assessment ?? null;
      state.suggestedAction = payload.suggested_next_action ?? null;
      state.confidence = payload.confidence ?? null;
      state.missingFields = payload.missing_fields || [];
    };

    builder
      .addCase(analyzeComplaint.fulfilled, updateRiskState)
      .addCase(analyzePdfComplaint.fulfilled, updateRiskState);
  },
});

export const {
  setRiskAssessment,
  updateRiskField,
  clearRiskAssessment,
} = riskSlice.actions;

export default riskSlice.reducer;
