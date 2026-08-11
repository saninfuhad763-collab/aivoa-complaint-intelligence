import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { complaintApi } from '../../services/complaintApi.js';
import { extractErrorMessage } from '../../services/apiClient.js';

// Async thunks for complaint operations
export const fetchComplaints = createAsyncThunk(
  'complaints/fetchComplaints',
  async (params, { rejectWithValue }) => {
    try {
      return await complaintApi.getComplaints(params);
    } catch (err) {
      return rejectWithValue(extractErrorMessage(err));
    }
  }
);

export const fetchComplaintById = createAsyncThunk(
  'complaints/fetchComplaintById',
  async (id, { rejectWithValue }) => {
    try {
      return await complaintApi.getComplaint(id);
    } catch (err) {
      return rejectWithValue(extractErrorMessage(err));
    }
  }
);

export const createNewComplaint = createAsyncThunk(
  'complaints/createNewComplaint',
  async (data, { rejectWithValue }) => {
    try {
      return await complaintApi.createComplaint(data);
    } catch (err) {
      return rejectWithValue(extractErrorMessage(err));
    }
  }
);

export const updateExistingComplaint = createAsyncThunk(
  'complaints/updateExistingComplaint',
  async ({ id, data }, { rejectWithValue }) => {
    try {
      return await complaintApi.updateComplaint(id, data);
    } catch (err) {
      return rejectWithValue(extractErrorMessage(err));
    }
  }
);

export const removeComplaint = createAsyncThunk(
  'complaints/removeComplaint',
  async (id, { rejectWithValue }) => {
    try {
      await complaintApi.deleteComplaint(id);
      return id;
    } catch (err) {
      return rejectWithValue(extractErrorMessage(err));
    }
  }
);

export const analyzeComplaint = createAsyncThunk(
  'complaints/analyzeComplaint',
  async (data, { rejectWithValue }) => {
    try {
      return await complaintApi.analyzeComplaint(data);
    } catch (err) {
      return rejectWithValue(extractErrorMessage(err));
    }
  }
);

export const analyzePdfComplaint = createAsyncThunk(
  'complaints/analyzePdfComplaint',
  async (file, { rejectWithValue }) => {
    try {
      return await complaintApi.analyzePdf(file);
    } catch (err) {
      return rejectWithValue(extractErrorMessage(err));
    }
  }
);

const initialState = {
  complaints: [],
  selectedComplaint: null,
  loading: false,
  error: null,
  analysisResult: null,
  analysisLoading: false,
  analysisError: null,
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
  filters: {
    status: null,
    severity: null,
    productName: null,
  },
};

const complaintSlice = createSlice({
  name: 'complaints',
  initialState,
  reducers: {
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
      state.pagination.page = 1; // Reset to page 1 on filter change
    },
    resetFilters: (state) => {
      state.filters = initialState.filters;
      state.pagination.page = 1;
    },
    setPagination: (state, action) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    clearSelectedComplaint: (state) => {
      state.selectedComplaint = null;
    },
    clearAnalysisResult: (state) => {
      state.analysisResult = null;
      state.analysisError = null;
    },
    clearError: (state) => {
      state.error = null;
      state.analysisError = null;
    },
    /**
     * patchAnalysisResult — merge targeted field corrections into the existing
     * analysisResult without running a full re-analysis.
     *
     * action.payload: { fields: { fieldName: value, ... } }
     *
     * Used by the Copilot follow-up handler to update individual fields
     * (e.g. batch_number, affected_quantity) while preserving all other
     * existing analysisResult state (risk assessment, confidence, etc.).
     *
     * CORE_COMPLAINT_FIELDS (backend): customer_name, product_name,
     * batch_number, complaint_type, complaint_description.
     * missing_fields is recomputed here so ComplaintnessChecker stays
     * accurate after a correction.
     */
    patchAnalysisResult: (state, action) => {
      if (!state.analysisResult) return;
      const CORE_FIELDS = [
        'customer_name',
        'product_name',
        'batch_number',
        'complaint_type',
        'complaint_description',
      ];
      const fields = action.payload?.fields || {};
      // Merge the corrected fields into the existing complaint_data
      state.analysisResult = {
        ...state.analysisResult,
        complaint_data: {
          ...(state.analysisResult.complaint_data || {}),
          ...fields,
        },
      };
      // Recompute missing_fields for the 5 core required fields
      const data = state.analysisResult.complaint_data;
      state.analysisResult.missing_fields = CORE_FIELDS.filter((f) => {
        const val = data[f];
        return val === null || val === undefined || val === '';
      });
    },
    /**
     * seedAnalysisResult — initialize a minimal analysisResult from a saved
     * complaint record when reopening, so ComplaintnessChecker can render
     * without any AI/LLM call.
     *
     * Unlike patchAnalysisResult, this always writes — even when analysisResult
     * is currently null (i.e. after a page refresh / new session).
     *
     * action.payload: { complaint_data: { ...fields } }
     */
    seedAnalysisResult: (state, action) => {
      const complaint_data = action.payload?.complaint_data || {};
      const CORE_FIELDS = [
        'customer_name',
        'product_name',
        'batch_number',
        'complaint_type',
        'complaint_description',
      ];
      const missing_fields = CORE_FIELDS.filter((f) => {
        const val = complaint_data[f];
        return val === null || val === undefined || val === '';
      });
      state.analysisResult = {
        complaint_data,
        missing_fields,
        validation_errors: [],
        // Preserve any other fields as empty — this is a restore, not a fresh analysis
        complaint_category: null,
        severity: null,
        risk_level: null,
        initial_risk_assessment: null,
        suggested_next_action: null,
        confidence: null,
        messages: [],
        document_metadata: null,
      };
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchComplaints
      .addCase(fetchComplaints.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchComplaints.fulfilled, (state, action) => {
        state.loading = false;
        state.complaints = action.payload.items || [];
        state.pagination.total = action.payload.total || 0;
        state.pagination.page = action.payload.page || 1;
        state.pagination.pageSize = action.payload.page_size || 20;
      })
      .addCase(fetchComplaints.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // fetchComplaintById
      .addCase(fetchComplaintById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchComplaintById.fulfilled, (state, action) => {
        state.loading = false;
        state.selectedComplaint = action.payload;
      })
      .addCase(fetchComplaintById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // createNewComplaint
      .addCase(createNewComplaint.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createNewComplaint.fulfilled, (state, action) => {
        state.loading = false;
        state.selectedComplaint = action.payload;
        state.complaints.unshift(action.payload);
        state.pagination.total += 1;
      })
      .addCase(createNewComplaint.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // updateExistingComplaint
      .addCase(updateExistingComplaint.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateExistingComplaint.fulfilled, (state, action) => {
        state.loading = false;
        state.selectedComplaint = action.payload;
        const index = state.complaints.findIndex((c) => c.id === action.payload.id);
        if (index !== -1) {
          state.complaints[index] = action.payload;
        }
      })
      .addCase(updateExistingComplaint.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // removeComplaint
      .addCase(removeComplaint.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeComplaint.fulfilled, (state, action) => {
        state.loading = false;
        const id = action.payload;
        state.complaints = state.complaints.filter((c) => c.id !== id);
        if (state.selectedComplaint?.id === id) {
          state.selectedComplaint = null;
        }
        state.pagination.total = Math.max(0, state.pagination.total - 1);
      })
      .addCase(removeComplaint.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // analyzeComplaint
      .addCase(analyzeComplaint.pending, (state) => {
        state.analysisLoading = true;
        state.analysisError = null;
      })
      .addCase(analyzeComplaint.fulfilled, (state, action) => {
        state.analysisLoading = false;
        state.analysisResult = action.payload;
      })
      .addCase(analyzeComplaint.rejected, (state, action) => {
        state.analysisLoading = false;
        state.analysisError = action.payload;
      })
      // analyzePdfComplaint
      .addCase(analyzePdfComplaint.pending, (state) => {
        state.analysisLoading = true;
        state.analysisError = null;
      })
      .addCase(analyzePdfComplaint.fulfilled, (state, action) => {
        state.analysisLoading = false;
        state.analysisResult = action.payload;
      })
      .addCase(analyzePdfComplaint.rejected, (state, action) => {
        state.analysisLoading = false;
        state.analysisError = action.payload;
      });
  },
});

export const {
  setFilters,
  resetFilters,
  setPagination,
  clearSelectedComplaint,
  clearAnalysisResult,
  clearError,
  patchAnalysisResult,
  seedAnalysisResult,
} = complaintSlice.actions;

export default complaintSlice.reducer;
