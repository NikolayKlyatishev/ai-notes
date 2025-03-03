/**
 * Конфигурация API для фронтенд-приложения
 */

// Базовый URL API
export const API_BASE_URL = 'http://localhost:8080';

// Эндпоинты API
export const API_ENDPOINTS = {
  // Аутентификация
  AUTH: {
    STATUS: '/api/auth/status',
    LOGIN_GOOGLE: '/api/auth/login/google',
    LOGIN_YANDEX: '/api/auth/login/yandex',
    LOGOUT: '/api/auth/logout',
    ME: '/api/auth/me',
  },
  // Заметки
  NOTES: {
    BASE: '/api/notes',
    LIST: '/api/notes/',
    GET: (id: string) => `/api/notes/${id}`,
    CREATE: '/api/notes/',
    UPDATE: (id: string) => `/api/notes/${id}`,
    DELETE: (id: string) => `/api/notes/${id}`,
  },
  // Поиск
  SEARCH: {
    QUERY: '/api/search/',
  },
  // Запись
  RECORDER: {
    BASE: '/api/recorder',
    START: '/api/recorder/start',
    STOP: '/api/recorder/stop',
    STATUS: '/api/recorder/status',
    RECORDINGS: '/api/recorder/recordings',
  },
  // Статус API
  STATUS: '/api/status',
}; 