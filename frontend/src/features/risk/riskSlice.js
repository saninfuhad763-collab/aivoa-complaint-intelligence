import { createSlice } from '@reduxjs/toolkit';

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
});

export const {
  setRiskAssessment,
  updateRiskField,
  clearRiskAssessment,
} = riskSlice.actions;

export default riskSlice.reducer;
