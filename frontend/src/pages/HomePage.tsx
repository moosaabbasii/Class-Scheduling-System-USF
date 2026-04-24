import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import SchedulesList from '../components/SchedulesList';
import { ApiClientError, type Schedule } from '../services/api';
import { useApiClient } from '../services/useApiClient';
import { useCurrentUser } from '../services/useCurrentUser';

export default function HomePage() {
    const api = useApiClient();
    const { currentUserId, setCurrentUserId } = useCurrentUser();
    const [schedules, setSchedules] = useState<Schedule[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;
        async function loadSchedules() {
            setIsLoading(true);
            setError(null);
            try {
                const response = await api.schedules.list();
                if (isMounted) {
                    setSchedules(response);
                }
            } catch (caughtError) {
                if (!isMounted) {
                    return;
                }
                if (caughtError instanceof ApiClientError) {
                    setError(caughtError.message);
                } else {
                    setError('Unable to load schedules. Verify the backend is running.');
                }
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        }
        loadSchedules();
        return () => {
            isMounted = false;
        };
    }, [api]);

    return (
        <div className="app-shell">
            <section className="page-header">
                <h1>Bellini College Scheduler</h1>
                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                    <label>
                        <input
                            checked={currentUserId === 1}
                            name="current-user-id"
                            onChange={() => setCurrentUserId(1)}
                            type="radio"
                        />
                        Committee Chair
                    </label>
                    <label>
                        <input
                            checked={currentUserId === 2}
                            name="current-user-id"
                            onChange={() => setCurrentUserId(2)}
                            type="radio"
                        />
                        Committee Member
                    </label>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                    <Link className="button-link" to="/reports">
                        Open Audit Reports
                    </Link>
                    {/* US5: Enrollment comparison — accessible to all roles */}
                    <Link className="button-link" to="/enrollment">
                        Enrollment Comparison
                    </Link>
                </div>
            </section>
            <section className="panel">
                <h2>Recent Schedules</h2>
                {isLoading ? <p>Loading schedules...</p> : null}
                {error ? <p className="form-message is-error">{error}</p> : null}
                {!isLoading && !error ? <SchedulesList schedules={schedules} /> : null}
            </section>
        </div>
    );
}
