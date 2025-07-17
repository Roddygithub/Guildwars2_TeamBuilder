import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

import config from '../config';

// Configuration de base d'Axios
const apiClient: AxiosInstance = axios.create({
  baseURL: config.api.baseUrl,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 10000, // 10 secondes de timeout
});

// Intercepteur pour les requêtes
apiClient.interceptors.request.use(
  (config) => {
    // Ici, vous pouvez ajouter des en-têtes d'authentification si nécessaire
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data || '');
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Intercepteur pour les réponses
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`[API] Response ${response.status} ${response.config.url}`, response.data);
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      // La requête a été faite et le serveur a répondu avec un code d'erreur
      console.error(
        `[API] Error ${error.response.status} ${error.config?.url}:`,
        error.response.data
      );
    } else if (error.request) {
      // La requête a été faite mais aucune réponse n'a été reçue
      console.error('[API] No response received:', error.request);
    } else {
      // Une erreur s'est produite lors de la configuration de la requête
      console.error('[API] Request setup error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Méthodes HTTP de base
const api = {
  get: <T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    apiClient.get<T>(url, config),
    
  post: <T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig<D>): Promise<AxiosResponse<T, D>> => 
    apiClient.post<T, AxiosResponse<T, D>, D>(url, data, config),
    
  put: <T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig<D>): Promise<AxiosResponse<T, D>> => 
    apiClient.put<T, AxiosResponse<T, D>, D>(url, data, config),
    
  delete: <T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    apiClient.delete<T>(url, config),
    
  // Méthodes spécifiques à l'application
  teams: {
    generate: (teamSize: number, playstyle: string) => 
      apiClient.post('/teams/generate', { team_size: teamSize, playstyle }),
  },
};

export default api;
