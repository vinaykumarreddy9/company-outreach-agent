const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Ensure it ends with a slash for consistent usage
const normalizedBaseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL : `${API_BASE_URL}/`;

export default normalizedBaseUrl;
