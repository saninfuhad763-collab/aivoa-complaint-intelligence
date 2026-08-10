import axios from 'axios';

const getBaseUrl = () => {
  try {
    return (import.meta && import.meta.env && import.meta.env.VITE_API_BASE_URL) || 'http://127.0.0.1:8000';
  } catch {
    return 'http://127.0.0.1:8000';
  }
};

const baseURL = getBaseUrl();

const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

/**
 * Standardized error extractor for API calls.
 */
export const extractErrorMessage = (error) => {
  if (error.response) {
    // Server responded with non-2xx status
    const detail = error.response.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail.map((err) => err.msg || JSON.stringify(err)).join('; ');
    }
    return error.response.data?.message || `Server error (${error.response.status})`;
  }
  if (error.request) {
    // Request made but no response received
    return 'Unable to connect to the server. Please check if the backend is running.';
  }
  return error.message || 'An unexpected error occurred.';
};

export default apiClient;
