import { useEffect, useState, type ReactNode } from 'react';
import { CurrentUserContext } from './CurrentUserStore';

type CurrentUserProviderProps = {
    children: ReactNode;
};

const STORAGE_KEY = 'bellini-current-user-id';

function getInitialCurrentUserId(): number {
    if (typeof window === 'undefined') {
        return 1;
    }

    const storedValue = window.localStorage.getItem(STORAGE_KEY);
    return storedValue === '2' ? 2 : 1;
}

export function CurrentUserProvider({ children }: CurrentUserProviderProps) {
    const [currentUserId, setCurrentUserId] = useState<number>(getInitialCurrentUserId);

    useEffect(() => {
        window.localStorage.setItem(STORAGE_KEY, String(currentUserId));
    }, [currentUserId]);

    return (
        <CurrentUserContext.Provider value={{ currentUserId, setCurrentUserId }}>
            {children}
        </CurrentUserContext.Provider>
    );
}
