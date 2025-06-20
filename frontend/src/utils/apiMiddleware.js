import axios from 'axios';
import { camelizeKeys, decamelizeKeys } from 'humps';

// TODO: make various for api version
const api = axios.create({
  baseURL: `http://${process.env.REACT_APP_BACKEND_HOST}:${process.env.REACT_APP_BACKEND_PORT}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    // Добавляем токен авторизации, если он есть
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    if (config.data) {
      config.data = decamelizeKeys(config.data);
    }
    
    if (config.params) {
      config.params = decamelizeKeys(config.params);
    }
    
    console.log('Request:', config);
    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    console.log('Response:', response);
    
    const processedData = camelizeKeys(response.data);
    
    return processedData;
  },
  (error) => {
    console.error('Response Error:', error.response?.data || error.message);
    
    if (error.response?.data) {
      error.response.data = camelizeKeys(error.response.data);
    }
    
    return Promise.reject(error);
  }
);

export default api;
