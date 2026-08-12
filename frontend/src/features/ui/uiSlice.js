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
      const { type = 'info', message } = action.payload;

      // Deduplicate: skip if an identical message+type is already visible
      const isDuplicate = state.notifications.some(
        (n) => n.type === type && n.message === message
      );
      if (isDuplicate) return;

      // Cap at 3 visible notifications — drop the oldest when over the limit
      if (state.notifications.length >= 3) {
        state.notifications.shift();
      }

      state.notifications.push({
        id: Date.now().toString(),
        type,
        message,
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
