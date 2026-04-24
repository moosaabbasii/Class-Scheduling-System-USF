import { useContext } from 'react';
import { CurrentUserContext } from './CurrentUserStore';

export function useCurrentUser() {
    const currentUser = useContext(CurrentUserContext);

    if (!currentUser) {
        throw new Error('useCurrentUser must be used within CurrentUserProvider.');
    }

    return currentUser;
}
