import { configureStore } from '@reduxjs/toolkit';
import complaintReducer from '../features/complaints/complaintSlice.js';
import copilotReducer from '../features/copilot/copilotSlice.js';
import riskReducer from '../features/risk/riskSlice.js';
import uiReducer from '../features/ui/uiSlice.js';

export const store = configureStore({
  reducer: {
    complaints: complaintReducer,
    copilot: copilotReducer,
    risk: riskReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export default store;
