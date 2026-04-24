import { useContext } from 'react';
import { ApiClientContext } from './ApiClientStore';

export function useApiClient() {
    const apiClient = useContext(ApiClientContext);

    if (!apiClient) {
        throw new Error('useApiClient must be used within ApiClientProvider.');
    }

    return apiClient;
}
