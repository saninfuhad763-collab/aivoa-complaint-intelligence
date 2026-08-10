import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  messages: [],
  input: '',
  loading: false,
  error: null,
};

const copilotSlice = createSlice({
  name: 'copilot',
  initialState,
  reducers: {
    setInput: (state, action) => {
      state.input = action.payload;
    },
    addMessage: (state, action) => {
      // action.payload: { role: 'user'|'assistant'|'system', content: string, timestamp?: string }
      state.messages.push({
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        ...action.payload,
      });
    },
    clearMessages: (state) => {
      state.messages = [];
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setInput,
  addMessage,
  clearMessages,
  setLoading,
  setError,
  clearError,
} = copilotSlice.actions;

export default copilotSlice.reducer;
