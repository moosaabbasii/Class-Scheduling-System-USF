import { useState, type ReactNode } from 'react';
import { createApiClient } from './api';
import { ApiClientContext } from './ApiClientStore';

type ApiClientProviderProps = {
    baseUrl: string;
    children: ReactNode;
};

export function ApiClientProvider({ baseUrl, children }: ApiClientProviderProps) {
    const [apiClient] = useState(() => createApiClient(baseUrl));

    return (
        <ApiClientContext.Provider value={apiClient}>{children}</ApiClientContext.Provider>
    );
}
