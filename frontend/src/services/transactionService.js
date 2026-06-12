import api from './api';

export const uploadStatement = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/transactions/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getTransactions = async (params = {}) => {
  const response = await api.get('/transactions', { params });
  return response.data;
};

export const getTransactionSummary = async (params = {}) => {
  const response = await api.get('/transactions/summary', { params });
  return response.data;
};

export const getCategories = async () => {
  const response = await api.get('/transactions/categories');
  return response.data;
};
