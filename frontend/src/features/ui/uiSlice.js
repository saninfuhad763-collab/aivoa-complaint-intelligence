import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  activePanel: 'form', // 'form' | 'copilot'
  notifications: [],
  isModalOpen: false,
  modalType: null,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setActivePanel: (state, action) => {
      state.activePanel = action.payload;
    },
    addNotification: (state, action) => {
      // action.payload: { type: 'success'|'error'|'info'|'warning', message: string }
      state.notifications.push({
        id: Date.now().toString(),
        type: action.payload.type || 'info',
        message: action.payload.message,
      });
    },
    removeNotification: (state, action) => {
      state.notifications = state.notifications.filter((n) => n.id !== action.payload);
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    toggleModal: (state, action) => {
      state.isModalOpen = action.payload?.open ?? !state.isModalOpen;
      state.modalType = action.payload?.type ?? null;
    },
  },
});

export const {
  setActivePanel,
  addNotification,
  removeNotification,
  clearNotifications,
  toggleModal,
} = uiSlice.actions;

export default uiSlice.reducer;
