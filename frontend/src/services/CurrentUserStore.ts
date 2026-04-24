import { createContext } from 'react';

export type CurrentUserContextValue = {
    currentUserId: number;
    setCurrentUserId: (nextUserId: number) => void;
};

export const CurrentUserContext = createContext<CurrentUserContextValue | null>(null);
