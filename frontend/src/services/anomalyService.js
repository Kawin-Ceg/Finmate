import api from './api';

export const getAnomalies = () =>
  api.get('/anomalies').then((r) => r.data);

export const getAnomalySummary = () =>
  api.get('/anomalies/summary').then((r) => r.data);

export const getAnomalyStats = () =>
  api.get('/anomalies/stats').then((r) => r.data);

export const getSubscriptions = () =>
  api.get('/anomalies/subscriptions').then((r) => r.data);

export const runAnomalyDetection = () =>
  api.post('/anomalies/run').then((r) => r.data);
