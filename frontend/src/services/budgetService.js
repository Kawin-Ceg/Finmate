import api from './api';

export const getBudgets = () =>
  api.get('/budgets').then((r) => r.data);

export const getBudgetOverview = () =>
  api.get('/budgets/overview').then((r) => r.data);

export const getBudgetForecast = () =>
  api.get('/budgets/forecast').then((r) => r.data);

export const createBudget = (data) =>
  api.post('/budgets', data).then((r) => r.data);

export const updateBudget = (id, data) =>
  api.put(`/budgets/${id}`, data).then((r) => r.data);

export const deleteBudget = (id) =>
  api.delete(`/budgets/${id}`);
