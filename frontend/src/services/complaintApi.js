import apiClient from './apiClient.js';

/**
 * Complaint API service endpoints matching the FastAPI backend contract.
 */
export const complaintApi = {
  /**
   * Create a new complaint.
   * POST /api/complaints
   */
  createComplaint: async (complaintData) => {
    const response = await apiClient.post('/api/complaints', complaintData);
    return response.data;
  },

  /**
   * Get paginated and filtered list of complaints.
   * GET /api/complaints
   * @param {Object} params - { page, page_size, status, severity, product_name }
   */
  getComplaints: async (params = {}) => {
    const response = await apiClient.get('/api/complaints', { params });
    return response.data;
  },

  /**
   * Get a single complaint by ID.
   * GET /api/complaints/{id}
   */
  getComplaint: async (id) => {
    const response = await apiClient.get(`/api/complaints/${id}`);
    return response.data;
  },

  /**
   * Perform partial update on a complaint by ID.
   * PATCH /api/complaints/{id}
   */
  updateComplaint: async (id, updateData) => {
    const response = await apiClient.patch(`/api/complaints/${id}`, updateData);
    return response.data;
  },

  /**
   * Delete a complaint by ID.
   * DELETE /api/complaints/{id}
   */
  deleteComplaint: async (id) => {
    const response = await apiClient.delete(`/api/complaints/${id}`);
    return response.data;
  },

  /**
   * Perform AI analysis on raw complaint input.
   * POST /api/complaints/analyze
   * @param {Object} data - { input_text, source_type }
   */
  analyzeComplaint: async (data) => {
    const response = await apiClient.post('/api/complaints/analyze', data);
    return response.data;
  },
};

export default complaintApi;
