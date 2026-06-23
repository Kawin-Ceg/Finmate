import api from './api';

export const getOverview = () =>
  api.get('/analytics/overview').then(r => r.data);

export const getMonthlyTrend = () =>
  api.get('/analytics/monthly-trend').then(r => r.data);

export const getCategoryBreakdown = () =>
  api.get('/analytics/category-breakdown').then(r => r.data);

export const getTopMerchants = () =>
  api.get('/analytics/top-merchants').then(r => r.data);

export const getCashflow = () =>
  api.get('/analytics/cashflow').then(r => r.data);

export const getHeatmap = () =>
  api.get('/analytics/heatmap').then(r => r.data);

export const getHealthScore = () =>
  api.get('/analytics/health-score').then(r => r.data);

// Consolidated payload for the dashboard landing page — replaces 7 separate
// calls (health-score, overview, budget forecast, anomalies, category
// breakdown, monthly trend, top merchants) with a single round trip.
export const getDashboardOverview = () =>
  api.get('/dashboard/overview').then(r => r.data);
