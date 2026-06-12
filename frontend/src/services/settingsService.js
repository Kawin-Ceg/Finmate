import api from './api';

export const getSettings = () =>
  api.get('/settings').then((r) => r.data);

export const updateSettings = (data) =>
  api.put('/settings', data).then((r) => r.data);

export const getSessions = () =>
  api.get('/security/sessions').then((r) => r.data);

export const revokeSession = (id) =>
  api.delete(`/security/sessions/${id}`).then((r) => r.data);

export const revokeAllOtherSessions = () =>
  api.delete('/security/sessions').then((r) => r.data);

export const exportData = (format = 'csv') =>
  api.post('/account/export', { format }, { responseType: 'blob' }).then((r) => r.data);

export const deleteAccount = (password) =>
  api.delete('/account', { data: { password } }).then((r) => r.data);
