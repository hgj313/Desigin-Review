import axios from 'axios';
import type { Report, UploadResponse, ReviewRequest } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

export const upload = async (formData: FormData): Promise<UploadResponse> => {
  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const triggerReview = async (req: ReviewRequest): Promise<Report> => {
  const response = await api.post<Report>('/review', req);
  return response.data;
};

export const getReport = async (reportId: string): Promise<Report> => {
  const response = await api.get<Report>(`/reports/${reportId}`);
  return response.data;
};

export const listReports = async (): Promise<Report[]> => {
  const response = await api.get<Report[]>('/reports');
  return response.data;
};

export const healthCheck = async (): Promise<{ status: string }> => {
  const response = await api.get<{ status: string }>('/health');
  return response.data;
};

export default api;