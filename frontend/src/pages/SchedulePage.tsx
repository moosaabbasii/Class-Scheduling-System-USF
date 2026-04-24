import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ClassScheduleTable } from '../components/ClassScheduleTable';
import { PageHeader } from '../components/PageHeader';
import { RoomReservationHeatmap } from '../components/RoomReservationHeatmap';
import { ApiClientError, type CourseSection, type Room, type Schedule } from '../services/api';
import { useApiClient } from '../services/useApiClient';
import { useCurrentUser } from '../services/useCurrentUser';

export function SchedulePage() {
    const [classes, setClasses] = useState<CourseSection[]>([]);
    const [query, setQuery] = useState('');
    const [rooms, setRooms] = useState<Room[]>([]);
    const [schedule, setSchedule] = useState<Schedule | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [lockError, setLockError] = useState<string | null>(null);
    const [lockSuccess, setLockSuccess] = useState<string | null>(null);
    const [isLocking, setIsLocking] = useState(false);
    const [activeView, setActiveView] = useState<'classes' | 'rooms'>('classes');
    const params = useParams();
    const api = useApiClient();
    const { currentUserId } = useCurrentUser();

    // currentUserId === 1 is the Chair (can lock/unlock)
    const isChair = currentUserId === 1;

    useEffect(() => {
        const fetchSchedule = async () => {
            setError(null);

            try {
                setSchedule(await api.schedules.getById(Number.parseInt(params.scheduleId!)));
                setClasses(await api.schedules.listSections(Number.parseInt(params.scheduleId!)));
                setRooms(await api.lookups.rooms.list());
            } catch (caughtError) {
                if (caughtError instanceof ApiClientError) {
                    setError(caughtError.message);
                    return;
                }

                setError('Unable to load schedule details.');
            }
        };

        fetchSchedule();
    }, [api, params.scheduleId]);

    const filteredClasses = useMemo(() => {
        const trimmed = query.trim().toLowerCase();
        if (!trimmed) {
            return classes;
        }

        return classes.filter((item) => {
            return (
                item.crn.toString().includes(trimmed) ||
                item.course_number?.toLowerCase().includes(trimmed) ||
                item.course_title?.toLowerCase().includes(trimmed) ||
                item.instructor_name?.toLowerCase().includes(trimmed) ||
                item.room_number?.toLowerCase().includes(trimmed)
            );
        });
    }, [classes, query]);

    const handleDelete = async (id: number, className: string) => {
        if (window.confirm(`Are you sure you want to delete ${className}?`)) {
            setError(null);

            try {
                await api.sections.delete(id, currentUserId);
                setClasses((previous) => previous.filter((item) => item.id !== id));
            } catch (caughtError) {
                if (caughtError instanceof ApiClientError) {
                    setError(caughtError.message);
                    return;
                }

                setError('Unable to delete class.');
            }
        }
    };

    // ── US6: Lock / Unlock ──────────────────────────────────────────────────
    const handleLockToggle = async () => {
        if (!schedule) return;

        const action = schedule.locked ? 'unlock' : 'lock';
        const confirmed = window.confirm(
            schedule.locked
                ? 'Unlock this schedule? Edits will be allowed again.'
                : 'Lock this schedule? No edits can be made until it is unlocked.',
        );
        if (!confirmed) return;

        setIsLocking(true);
        setLockError(null);
        setLockSuccess(null);

        try {
            const updated =
                action === 'lock'
                    ? await api.schedules.lock(schedule.id, currentUserId)
                    : await api.schedules.unlock(schedule.id, currentUserId);

            setSchedule(updated);
            setLockSuccess(
                action === 'lock'
                    ? 'Schedule locked. No further edits are allowed.'
                    : 'Schedule unlocked. Edits are now allowed.',
            );
        } catch (caughtError) {
            if (caughtError instanceof ApiClientError) {
                setLockError(caughtError.message);
            } else {
                setLockError(`Unable to ${action} schedule.`);
            }
        } finally {
            setIsLocking(false);
        }
    };

    return (
        <div className="app-shell">
            <PageHeader
                title={schedule?.name || 'Loading...'}
                eyebrow="Schedule editor"
                subtitle="Add, search, edit or remove classes from this schedule"
            />

            <div className="schedule-workspace">
                <aside className="panel schedule-sidebar">
                    <h2>Schedule Views</h2>
                    <div
                        className="schedule-nav"
                        role="tablist"
                        aria-label="Schedule content sections">
                        <button
                            aria-selected={activeView === 'classes'}
                            className={
                                activeView === 'classes'
                                    ? 'schedule-nav-button is-active'
                                    : 'schedule-nav-button'
                            }
                            onClick={() => setActiveView('classes')}
                            role="tab"
                            type="button">
                            Classes List
                        </button>
                        <button
                            aria-selected={activeView === 'rooms'}
                            className={
                                activeView === 'rooms'
                                    ? 'schedule-nav-button is-active'
                                    : 'schedule-nav-button'
                            }
                            onClick={() => setActiveView('rooms')}
                            role="tab"
                            type="button">
                            Room Utilization
                        </button>
                        {currentUserId === 1 && (
                            <Link className="schedule-nav-button" to="/reports">
                                Audit Reports
                            </Link>
                        )}
                    </div>

                    {/* ── US6: Lock / Unlock section (chair only) ── */}
                    {isChair && schedule && (
                        <div style={{ marginTop: '1.5rem' }}>
                            <h2>Schedule Status</h2>
                            <p style={{ margin: '0 0 0.5rem', fontSize: '0.9rem', color: '#4b5563' }}>
                                {schedule.locked
                                    ? '🔒 This schedule is locked. No edits are allowed.'
                                    : '🔓 This schedule is unlocked. Edits are allowed.'}
                            </p>
                            <button
                                className={schedule.locked ? 'button-secondary' : 'button-danger'}
                                disabled={isLocking}
                                onClick={handleLockToggle}
                                style={{ width: '100%' }}
                                type="button">
                                {isLocking
                                    ? schedule.locked
                                        ? 'Unlocking...'
                                        : 'Locking...'
                                    : schedule.locked
                                      ? 'Unlock Schedule'
                                      : 'Lock Schedule'}
                            </button>
                            {lockSuccess && (
                                <p className="form-message is-success">{lockSuccess}</p>
                            )}
                            {lockError && (
                                <p className="form-message is-error">{lockError}</p>
                            )}
                        </div>
                    )}
                </aside>

                {activeView === 'rooms' ? (
                    <section className="panel">
                        <div className="panel-head">
                            <h2>Room Utilization Heat Map</h2>
                        </div>
                        <RoomReservationHeatmap classes={classes} rooms={rooms} />
                    </section>
                ) : (
                    <section className="panel">
                        <div className="panel-head">
                            <h2>Existing Classes</h2>
                            <div className="panel-actions">
                                <input
                                    aria-label="Search classes"
                                    className="search-input"
                                    onChange={(event) => setQuery(event.target.value)}
                                    placeholder="Search by course, room, instructor..."
                                    type="search"
                                    value={query}
                                />
                                {!schedule?.locked && (
                                    <Link
                                        className="button-link"
                                        to={`/schedules/${params.scheduleId}/create-class`}>
                                        Create Class
                                    </Link>
                                )}
                            </div>
                        </div>

                        {schedule?.locked && (
                            <p className="form-message is-error" style={{ marginBottom: '0.75rem' }}>
                                🔒 This schedule is locked. Delete and edit actions are disabled.
                            </p>
                        )}

                        <ClassScheduleTable
                            classes={filteredClasses}
                            onDelete={schedule?.locked ? undefined : handleDelete}
                        />
                        {error ? <p className="form-message is-error">{error}</p> : null}
                    </section>
                )}
            </div>
        </div>
    );
}
