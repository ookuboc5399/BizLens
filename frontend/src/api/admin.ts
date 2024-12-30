import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/admin';

export const getFinancialData = async () => {
  const response = await axios.get(`${API_BASE_URL}/companies`);
  return response.data;
};

export const collectData = async (symbols: string[]) => {
  const response = await axios.post(`${API_BASE_URL}/data/collect`, { symbols });
  return response.data;
};