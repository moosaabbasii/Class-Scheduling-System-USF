import { createContext } from 'react';
import { createApiClient } from './api';

export type ApiClient = ReturnType<typeof createApiClient>;

export const ApiClientContext = createContext<ApiClient | null>(null);
