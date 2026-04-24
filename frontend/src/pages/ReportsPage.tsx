import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import {
    ApiClientError,
    type AuditIssue,
    type AuditReport,
    type Schedule,
} from '../services/api';
import { useApiClient } from '../services/useApiClient';
import { useCurrentUser } from '../services/useCurrentUser';
import styles from './ReportsPage.module.css';

const ISSUE_LABELS: Record<string, string> = {
    duplicate_crn: 'Duplicate CRN',
    duplicate_meeting_slot: 'Duplicate meeting slot',
    instructor_conflict: 'Instructor overlap',
    invalid_crn: 'Invalid CRN',
    invalid_date_format: 'Invalid date format',
    invalid_date_range: 'Invalid date range',
    invalid_meeting_days: 'Invalid meeting days',
    invalid_meeting_range: 'Invalid meeting range',
    invalid_meeting_time_format: 'Invalid meeting time',
    missing_instructor: 'Missing instructor',
    missing_meetings: 'Missing meetings',
    missing_room: 'Missing room',
    room_capacity: 'Over capacity',
    room_conflict: 'Room overlap',
    section_meeting_conflict: 'Internal meeting overlap',
    ta_overallocated: 'TA overallocation',
    unreasonable_meeting_duration: 'Unreasonable duration',
    unreasonable_meeting_hours: 'Unreasonable meeting hours',
};

function formatDateTime(value: string) {
    const parsed = new Date(value);

    if (Number.isNaN(parsed.getTime())) {
        return value;
    }

    return parsed.toLocaleString();
}

function toIssueGroups(issues: AuditIssue[]) {
    const groups = new Map<string, AuditIssue[]>();

    for (const issue of issues) {
        const items = groups.get(issue.type) ?? [];
        items.push(issue);
        groups.set(issue.type, items);
    }

    return Array.from(groups.entries()).sort((left, right) => right[1].length - left[1].length);
}

function downloadBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
}

export default function ReportsPage() {
    const api = useApiClient();
    const { currentUserId } = useCurrentUser();
    const [schedules, setSchedules] = useState<Schedule[]>([]);
    const [reports, setReports] = useState<AuditReport[]>([]);
    const [selectedScheduleId, setSelectedScheduleId] = useState<number | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isRunningAudit, setIsRunningAudit] = useState(false);
    const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

    useEffect(() => {
        let isMounted = true;

        async function loadPage() {
            setIsLoading(true);
            setError(null);

            try {
                const [scheduleResponse, reportResponse] = await Promise.all([
                    api.schedules.list(),
                    api.audits.list(),
                ]);

                if (!isMounted) {
                    return;
                }

                setSchedules(scheduleResponse);
                setReports(reportResponse);

                const initialScheduleId =
                    reportResponse[0]?.schedule_id ?? scheduleResponse[0]?.id ?? null;
                setSelectedScheduleId(initialScheduleId);
            } catch (caughtError) {
                if (!isMounted) {
                    return;
                }

                if (caughtError instanceof ApiClientError) {
                    setError(caughtError.message);
                } else {
                    setError('Unable to load audit reports.');
                }
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        }

        loadPage();

        return () => {
            isMounted = false;
        };
    }, [api]);

    const selectedSchedule = useMemo(
        () => schedules.find((schedule) => schedule.id === selectedScheduleId) ?? null,
        [schedules, selectedScheduleId],
    );

    const selectedScheduleReports = useMemo(
        () => reports.filter((report) => report.schedule_id === selectedScheduleId),
        [reports, selectedScheduleId],
    );

    const latestReport = selectedScheduleReports[0] ?? null;
    const latestReportIssues = latestReport?.issues ?? [];
    const groupedIssues = useMemo(() => toIssueGroups(latestReportIssues), [latestReportIssues]);
    const openIssueCount =
        latestReportIssues.filter((issue) => issue.status === 'open').length;
    const resolvedIssueCount =
        latestReportIssues.filter((issue) => issue.status === 'resolved').length;

    const handleRunAudit = async () => {
        if (!selectedScheduleId) {
            setError('Select a schedule before running an audit.');
            return;
        }

        setIsRunningAudit(true);
        setError(null);

        try {
            const created = await api.audits.runForSchedule(
                selectedScheduleId,
                currentUserId,
                currentUserId,
            );
            setReports((previous) => [created, ...previous]);
        } catch (caughtError) {
            if (caughtError instanceof ApiClientError) {
                setError(caughtError.message);
            } else {
                setError('Unable to run the audit report.');
            }
        } finally {
            setIsRunningAudit(false);
        }
    };

    const handleDownloadPdf = async () => {
        if (!latestReport) {
            return;
        }

        setIsDownloadingPdf(true);
        setError(null);

        try {
            const blob = await api.exports.auditPdf(latestReport.id, currentUserId);
            downloadBlob(blob, `audit-report-${latestReport.id}.pdf`);
        } catch (caughtError) {
            if (caughtError instanceof ApiClientError) {
                setError(caughtError.message);
            } else {
                setError('Unable to export the audit PDF.');
            }
        } finally {
            setIsDownloadingPdf(false);
        }
    };

    return (
        <div className="app-shell">
            <PageHeader
                title="Audit Reports"
                eyebrow="Schedule QA"
                subtitle="Review inconsistent or invalid schedule data before release.">
                <div className={styles.headerActions}>
                    <Link className="button-link" to="/">
                        All Schedules
                    </Link>
                </div>
            </PageHeader>

            <section className={`panel ${styles.controlsPanel}`}>
                <div className={styles.controlRow}>
                    <label className={styles.field}>
                        <span>Schedule</span>
                        <select
                            onChange={(event) =>
                                setSelectedScheduleId(Number.parseInt(event.target.value, 10))
                            }
                            value={selectedScheduleId ?? ''}>
                            {schedules.length === 0 ? (
                                <option value="">No schedules available</option>
                            ) : null}
                            {schedules.map((schedule) => (
                                <option key={schedule.id} value={schedule.id}>
                                    {schedule.name}
                                </option>
                            ))}
                        </select>
                    </label>

                    <div className={styles.actions}>
                        <button
                            disabled={currentUserId !== 1 || !selectedScheduleId || isRunningAudit}
                            onClick={handleRunAudit}
                            type="button">
                            {isRunningAudit ? 'Running audit...' : 'Run Audit'}
                        </button>
                        <button
                            className="button-secondary"
                            disabled={!latestReport || isDownloadingPdf}
                            onClick={handleDownloadPdf}
                            type="button">
                            {isDownloadingPdf ? 'Exporting...' : 'Export PDF'}
                        </button>
                    </div>
                </div>

                {currentUserId !== 1 ? (
                    <p className={styles.helperText}>
                        Only the committee chair can generate a new report. Existing results
                        remain visible.
                    </p>
                ) : null}
                {error ? <p className="form-message is-error">{error}</p> : null}
            </section>

            {isLoading ? <section className="panel">Loading audit reports...</section> : null}

            {!isLoading && selectedSchedule ? (
                <>
                    <section className={`panel ${styles.summaryPanel}`}>
                        <div className={styles.summaryGrid}>
                            <article className={styles.summaryCard}>
                                <span className={styles.summaryLabel}>Schedule</span>
                                <strong>{selectedSchedule.name}</strong>
                                <span className={styles.summaryMeta}>
                                    Status: {selectedSchedule.status}
                                </span>
                            </article>
                            <article className={styles.summaryCard}>
                                <span className={styles.summaryLabel}>Latest report</span>
                                <strong>
                                    {latestReport ? `#${latestReport.id}` : 'None yet'}
                                </strong>
                                <span className={styles.summaryMeta}>
                                    {latestReport
                                        ? `Created ${formatDateTime(latestReport.created_at)}`
                                        : 'Run an audit to generate findings'}
                                </span>
                            </article>
                            <article className={styles.summaryCard}>
                                <span className={styles.summaryLabel}>Open issues</span>
                                <strong>{latestReport ? openIssueCount : 0}</strong>
                                <span className={styles.summaryMeta}>
                                    Resolved: {latestReport ? resolvedIssueCount : 0}
                                </span>
                            </article>
                        </div>
                    </section>

                    <section className={`panel ${styles.reportLayout}`}>
                        <div className={styles.reportColumn}>
                            <div className={styles.sectionHead}>
                                <h2>Latest Findings</h2>
                                {latestReport ? (
                                    <span
                                        className={styles.statusBadge}
                                        data-status={latestReport.status}>
                                        {latestReport.status}
                                    </span>
                                ) : null}
                            </div>

                            {!latestReport ? (
                                <p className="empty-state">
                                    No report exists for this schedule yet.
                                </p>
                            ) : latestReport.issues.length === 0 ? (
                                <p className="empty-state">
                                    No issues detected in the latest audit.
                                </p>
                            ) : (
                                <div className={styles.issueGroups}>
                                    {groupedIssues.map(([issueType, issues]) => (
                                        <article className={styles.issueGroup} key={issueType}>
                                            <div className={styles.issueGroupHead}>
                                                <h3>{ISSUE_LABELS[issueType] ?? issueType}</h3>
                                                <span>{issues.length}</span>
                                            </div>
                                            <ul className={styles.issueList}>
                                                {issues.map((issue) => (
                                                    <li
                                                        className={styles.issueCard}
                                                        key={issue.id}>
                                                        <p>{issue.description}</p>
                                                        <div className={styles.issueMeta}>
                                                            <span>
                                                                Detected{' '}
                                                                {formatDateTime(issue.detected_at)}
                                                            </span>
                                                            {issue.section_id ? (
                                                                <span>
                                                                    Section #{issue.section_id}
                                                                </span>
                                                            ) : null}
                                                        </div>
                                                    </li>
                                                ))}
                                            </ul>
                                        </article>
                                    ))}
                                </div>
                            )}
                        </div>

                        <aside className={styles.historyColumn}>
                            <div className={styles.sectionHead}>
                                <h2>Recent Reports</h2>
                            </div>
                            {selectedScheduleReports.length === 0 ? (
                                <p className="empty-state">No reports found for this schedule.</p>
                            ) : (
                                <ul className={styles.historyList}>
                                    {selectedScheduleReports.map((report) => (
                                        <li className={styles.historyItem} key={report.id}>
                                            <div>
                                                <strong>Report #{report.id}</strong>
                                                <p>{formatDateTime(report.created_at)}</p>
                                            </div>
                                            <div className={styles.historyMeta}>
                                                <span>{report.issues.length} issues</span>
                                                <span
                                                    className={styles.statusBadge}
                                                    data-status={report.status}>
                                                    {report.status}
                                                </span>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </aside>
                    </section>
                </>
            ) : null}
        </div>
    );
}
