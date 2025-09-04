import { useAuth } from '../AuthContext';

// Additional auth-related hooks can be added here
export const useAuthHeaders = () => {
  const { getAuthHeaders } = useAuth();
  return getAuthHeaders;
};

export const useAuthenticatedFetch = () => {
  const { getAuthHeaders } = useAuth();

  return async (url, options = {}) => {
    const headers = {
      ...getAuthHeaders(),
      ...options.headers,
    };

    return fetch(url, {
      ...options,
      headers,
    });
  };
};
