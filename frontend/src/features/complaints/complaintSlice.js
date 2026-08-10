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

const initialState = {
  complaints: [],
  selectedComplaint: null,
  loading: false,
  error: null,
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
    clearError: (state) => {
      state.error = null;
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
      });
  },
});

export const {
  setFilters,
  resetFilters,
  setPagination,
  clearSelectedComplaint,
  clearError,
} = complaintSlice.actions;

export default complaintSlice.reducer;
