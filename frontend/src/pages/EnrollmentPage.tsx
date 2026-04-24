import { useEffect, useState } from 'react';
import { PageHeader } from '../components/PageHeader';
import { ApiClientError, type Schedule } from '../services/api';
import { useApiClient } from '../services/useApiClient';
import { useCurrentUser } from '../services/useCurrentUser';

type EnrollmentRow = {
    course_number: string;
    title: string;
    [scheduleId: number]: {
        enrollment: number;
        section_count: number;
        near_capacity: boolean;
        significant_growth: boolean;
        offered: boolean;
    };
};

export default function EnrollmentPage() {
    const api = useApiClient();
    const { currentUserId } = useCurrentUser();

    const [schedules, setSchedules] = useState<Schedule[]>([]);
    const [selectedIds, setSelectedIds] = useState<number[]>([]);
    const [subject, setSubject] = useState('');
    const [courseNumber, setCourseNumber] = useState('');
    const [rows, setRows] = useState<EnrollmentRow[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [hasSearched, setHasSearched] = useState(false);

    // Load all schedules for the selector
    useEffect(() => {
        api.schedules.list().then(setSchedules).catch(() => {});
    }, [api]);

    const toggleSchedule = (id: number) => {
        setSelectedIds((prev) =>
            prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
        );
        // Clear results when selection changes — stale data from a different
        // set of schedules would show wrong "Not offered" values
        setRows([]);
        setHasSearched(false);
        setError(null);
    };

    const handleCompare = async () => {
        if (selectedIds.length < 2) {
            setError('Please select at least two schedules to compare.');
            return;
        }

        setIsLoading(true);
        setError(null);
        setHasSearched(true);

        try {
            const result = await api.analytics.enrollmentComparison({
                actorUserId: currentUserId,
                scheduleIds: selectedIds,
                subject: subject.trim() || undefined,
                courseNumber: courseNumber.trim() || undefined,
            });

            // result is an array of course objects from the API
            // shape: { course_number, title, semesters: { [scheduleId]: {...} } }
            setRows((result as any[]).map((item: any) => {
                const row: any = {
                    course_number: item.course_number,
                    title: item.title,
                };
                // API returns semesters as an array — find by schedule_id
                const semestersArray: any[] = Array.isArray(item.semesters) ? item.semesters : [];
                for (const schedId of selectedIds) {
                    const sem = semestersArray.find((s: any) => s.schedule_id === schedId) ?? null;
                    row[schedId] = sem
                        ? {
                              enrollment: sem.total_enrollment ?? 0,
                              section_count: sem.section_count ?? 0,
                              near_capacity: sem.near_capacity ?? false,
                              significant_growth: sem.significant_growth ?? false,
                              offered: sem.offered ?? true,
                          }
                        : { offered: false, enrollment: 0, section_count: 0, near_capacity: false, significant_growth: false };
                }
                return row as EnrollmentRow;
            }));
        } catch (caughtError) {
            if (caughtError instanceof ApiClientError) {
                setError(caughtError.message);
            } else {
                setError('Unable to load enrollment data.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportPdf = async () => {
        if (selectedIds.length < 2) return;

        setIsExporting(true);
        setError(null);

        try {
            const blob = await api.exports.analyticsComparisonPdf({
                actorUserId: currentUserId,
                scheduleIds: selectedIds,
                subject: subject.trim() || undefined,
                courseNumber: courseNumber.trim() || undefined,
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'enrollment-comparison.pdf';
            a.click();
            URL.revokeObjectURL(url);
        } catch (caughtError) {
            if (caughtError instanceof ApiClientError) {
                setError(caughtError.message);
            } else {
                setError('Unable to export PDF.');
            }
        } finally {
            setIsExporting(false);
        }
    };

    const selectedSchedules = schedules.filter((s) => selectedIds.includes(s.id));

    return (
        <div className="app-shell">
            <PageHeader
                eyebrow="Analytics"
                subtitle="Select two or more schedules to compare enrollment trends across semesters"
                title="Enrollment Comparison"
            />

            {/* ── Filter panel ── */}
            <section className="panel">
                <h2>Select Schedules & Filters</h2>

                {schedules.length === 0 && (
                    <p className="empty-state">No schedules available.</p>
                )}

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
                    {schedules.map((s) => (
                        <label
                            key={s.id}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.4rem',
                                padding: '0.4rem 0.75rem',
                                border: '1px solid',
                                borderColor: selectedIds.includes(s.id) ? '#2f5a9e' : '#c9d2dd',
                                borderRadius: '6px',
                                background: selectedIds.includes(s.id) ? '#eef4ff' : '#fff',
                                cursor: 'pointer',
                                userSelect: 'none',
                            }}>
                            <input
                                checked={selectedIds.includes(s.id)}
                                onChange={() => toggleSchedule(s.id)}
                                type="checkbox"
                            />
                            {s.name}
                            {s.locked && ' 🔒'}
                        </label>
                    ))}
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: '#4b5563' }}>
                            Subject (optional)
                        </label>
                        <input
                            onChange={(e) => setSubject(e.target.value)}
                            placeholder="e.g. COP"
                            value={subject}
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: '#4b5563' }}>
                            Course Number (optional)
                        </label>
                        <input
                            onChange={(e) => setCourseNumber(e.target.value)}
                            placeholder="e.g. 4331"
                            value={courseNumber}
                        />
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                        disabled={isLoading || selectedIds.length < 2}
                        onClick={handleCompare}
                        type="button">
                        {isLoading ? 'Loading...' : 'Compare'}
                    </button>
                    {hasSearched && rows.length > 0 && (
                        <button
                            className="button-secondary"
                            disabled={isExporting}
                            onClick={handleExportPdf}
                            type="button">
                            {isExporting ? 'Exporting...' : 'Export PDF'}
                        </button>
                    )}
                </div>

                {error && <p className="form-message is-error">{error}</p>}
            </section>

            {/* ── Results grid ── */}
            {hasSearched && !isLoading && (
                <section className="panel">
                    <div className="panel-head">
                        <h2>Results</h2>
                        {rows.length > 0 && (
                            <p style={{ margin: 0, fontSize: '0.85rem', color: '#4b5563' }}>
                                {rows.length} course{rows.length !== 1 ? 's' : ''} found
                                &nbsp;·&nbsp;
                                <span style={{ color: '#b45309' }}>🔴 = near capacity</span>
                                &nbsp;·&nbsp;
                                <span style={{ color: '#15803d' }}>📈 = significant growth</span>
                            </p>
                        )}
                    </div>

                    {rows.length === 0 ? (
                        <p className="empty-state">No courses found for the selected filters.</p>
                    ) : (
                        <div className="table-wrap">
                            <table className="simple-table">
                                <thead>
                                    <tr>
                                        <th>Course</th>
                                        <th>Title</th>
                                        {selectedSchedules.map((s) => (
                                            <th key={s.id}>{s.name}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows.map((row) => (
                                        <tr key={row.course_number}>
                                            <td>
                                                <strong>{row.course_number}</strong>
                                            </td>
                                            <td>{row.title}</td>
                                            {selectedSchedules.map((s) => {
                                                const cell = row[s.id];
                                                if (!cell || !cell.offered) {
                                                    return (
                                                        <td
                                                            key={s.id}
                                                            style={{ color: '#9ca3af', fontStyle: 'italic' }}>
                                                            Not offered
                                                        </td>
                                                    );
                                                }
                                                return (
                                                    <td key={s.id}>
                                                        <div>
                                                            <strong>{cell.enrollment}</strong> enrolled
                                                            {cell.near_capacity && (
                                                                <span
                                                                    style={{ marginLeft: '0.4rem', color: '#b45309' }}
                                                                    title="Near capacity">
                                                                    🔴
                                                                </span>
                                                            )}
                                                            {cell.significant_growth && (
                                                                <span
                                                                    style={{ marginLeft: '0.4rem', color: '#15803d' }}
                                                                    title="Significant growth">
                                                                    📈
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div style={{ fontSize: '0.82rem', color: '#6b7280' }}>
                                                            {cell.section_count} section{cell.section_count !== 1 ? 's' : ''}
                                                        </div>
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>
            )}
        </div>
    );
}
