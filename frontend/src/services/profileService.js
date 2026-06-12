import api from './api';

export const getProfile = () =>
  api.get('/profile').then((r) => r.data);

export const updateProfile = (data) =>
  api.put('/profile', data).then((r) => r.data);

export const uploadAvatar = (file) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/profile/avatar', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
};

export const deleteAvatar = () =>
  api.delete('/profile/avatar').then((r) => r.data);

export const getSecurityScore = () =>
  api.get('/profile/security-score').then((r) => r.data);

export const sendVerificationOTP = () =>
  api.post('/auth/send-verification-otp').then((r) => r.data);

export const verifyEmail = (otp) =>
  api.post('/auth/verify-email', { otp }).then((r) => r.data);

export const resendOTP = () =>
  api.post('/auth/resend-otp').then((r) => r.data);

export const changePassword = (data) =>
  api.post('/auth/change-password', data).then((r) => r.data);
