const API_BASE_URL = 'http://localhost:8000/api/admin';

export const getFinancialData = async () => {
  const response = await fetch(`${API_BASE_URL}/companies`);
  return response.json();
};

export const collectData = async (symbols: string[]) => {
  const response = await fetch(`${API_BASE_URL}/data/collect`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ symbols }),
  });
  return response.json();
};