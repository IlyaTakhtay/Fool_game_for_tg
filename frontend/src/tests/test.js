const apiUrl = process.env.BACKED_API_URL;

// Пример запроса к API
async function fetchData() {
  const response = await fetch(`${apiUrl}/your-endpoint`);
  const data = await response.json();
  return data;
}
