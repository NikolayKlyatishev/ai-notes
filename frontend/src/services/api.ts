import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from '../config';

// Создаем экземпляр axios с базовым URL
const api = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true, // Для работы с куками аутентификации
});

// Типы данных
export interface Note {
    id: string;
    title: string;
    content: string;
    tags: string[];
    created_at: string;
    updated_at: string;
}

export interface User {
    id: string;
    username: string;
    email: string;
}

export interface SearchResult {
    notes: Note[];
    total: number;
}

export interface RecorderStatus {
    is_recording: boolean;
    duration: number;
}

export interface Recording {
    id: string;
    filename: string;
    duration: number;
    created_at: string;
    transcription?: string;
}

// API сервис
export const apiService = {
    // Аутентификация
    auth: {
        getStatus: async (): Promise<{ authenticated: boolean; user: User | null }> => {
            try {
                const response = await api.get(API_ENDPOINTS.AUTH.STATUS);
                return response.data;
            } catch (error) {
                return { authenticated: false, user: null };
            }
        },
        getUser: async (): Promise<User> => {
            const response = await api.get(API_ENDPOINTS.AUTH.ME);
            return response.data;
        },
        logout: async () => {
            const response = await api.post(API_ENDPOINTS.AUTH.LOGOUT);
            return response.data;
        },
    },

    // Заметки
    notes: {
        getAll: async (): Promise<Note[]> => {
            const response = await api.get(API_ENDPOINTS.NOTES.LIST);
            return response.data;
        },
        getById: async (id: string): Promise<Note> => {
            const response = await api.get(API_ENDPOINTS.NOTES.GET(id));
            return response.data;
        },
        create: async (note: Omit<Note, 'id' | 'created_at' | 'updated_at'>): Promise<Note> => {
            const response = await api.post(API_ENDPOINTS.NOTES.CREATE, note);
            return response.data;
        },
        update: async (id: string, note: Partial<Note>): Promise<Note> => {
            const response = await api.put(API_ENDPOINTS.NOTES.UPDATE(id), note);
            return response.data;
        },
        delete: async (id: string): Promise<void> => {
            await api.delete(API_ENDPOINTS.NOTES.DELETE(id));
        },
    },

    // Поиск
    search: {
        query: async (query: string): Promise<SearchResult> => {
            const response = await api.post(API_ENDPOINTS.SEARCH.QUERY, { q: query });
            return response.data;
        },
    },

    // Запись
    recorder: {
        start: async (): Promise<void> => {
            await api.post(API_ENDPOINTS.RECORDER.START);
        },
        stop: async (): Promise<void> => {
            await api.post(API_ENDPOINTS.RECORDER.STOP);
        },
        getStatus: async (): Promise<RecorderStatus> => {
            const response = await api.get(API_ENDPOINTS.RECORDER.STATUS);
            return response.data;
        },
        getRecordings: async (): Promise<Recording[]> => {
            const response = await api.get(API_ENDPOINTS.RECORDER.RECORDINGS);
            return response.data;
        },
    },

    // Статус API
    getStatus: async (): Promise<{ status: string; version: string; api: string }> => {
        const response = await api.get(API_ENDPOINTS.STATUS);
        return response.data;
    },
};

export default apiService; 