import api from './api';

export const sendMessage = (message, sessionId = null) =>
  api.post('/mate/chat', { message, session_id: sessionId }).then(r => r.data);

export const getSessions = () =>
  api.get('/mate/sessions').then(r => r.data);

export const createSession = () =>
  api.post('/mate/sessions').then(r => r.data);

export const getSession = (id) =>
  api.get(`/mate/sessions/${id}`).then(r => r.data);

export const renameSession = (id, title) =>
  api.put(`/mate/sessions/${id}`, { title }).then(r => r.data);

export const deleteSession = (id) =>
  api.delete(`/mate/sessions/${id}`).then(r => r.data);

export const deleteAllSessions = () =>
  api.delete('/mate/sessions').then(r => r.data);

export const searchChats = (q) =>
  api.get('/mate/search', { params: { q } }).then(r => r.data);

export const getSuggestions = () =>
  api.get('/mate/suggestions').then(r => r.data);

export const exportChats = async (format = 'markdown', sessionId = null) => {
  const response = await api.post(
    '/mate/export',
    { format, session_id: sessionId },
    { responseType: 'blob' },
  );
  const ext = format === 'json' ? 'json' : 'md';
  const url = URL.createObjectURL(response.data);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mate_conversations.${ext}`;
  a.click();
  URL.revokeObjectURL(url);
};
