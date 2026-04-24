import { useEffect, useMemo, useState } from 'react';
import type { CourseSection, Meeting } from '../services/api';
import { Link } from 'react-router-dom';
import styles from './ClassScheduleTable.module.css';

type ClassScheduleTableProps = {
    classes: CourseSection[];
    onDelete: (id: number, className: string) => void;
    onEdit?: (id: string) => void;
};

function TimeDateCell({ meetings }: { meetings: Meeting[] }) {
    if (!meetings || meetings.length == 0) return <span>No meetings</span>;

    return (
        <div>
            <div>
                {meetings.map((meeting) => {
                    return <div key={meeting.days}>{meeting.days}</div>;
                })}
            </div>
            <span>
                {meetings[0].start_time} - {meetings[0].end_time}
            </span>
        </div>
    );
}

function TaNamesCell({ taAssignments }: { taAssignments: CourseSection['ta_assignments'] }) {
    const taNames = taAssignments
        .map((assignment) => assignment.ta_name?.trim())
        .filter((name): name is string => Boolean(name));

    if (taNames.length === 0) {
        return <span>None</span>;
    }

    return (
        <div className={`${styles.cellEllipsis} ${styles.taList}`}>
            {taNames.map((name) => (
                <span key={name} className={styles.taName} title={name}>
                    {name}
                </span>
            ))}
        </div>
    );
}

export function ClassScheduleTable({ classes, onDelete, onEdit }: ClassScheduleTableProps) {
    const PAGE_SIZE = 10;
    const [page, setPage] = useState(1);

    const totalPages = Math.max(1, Math.ceil(classes.length / PAGE_SIZE));
    const paginatedClasses = useMemo(() => {
        const start = (page - 1) * PAGE_SIZE;
        return classes.slice(start, start + PAGE_SIZE);
    }, [classes, page]);

    useEffect(() => {
        setPage((current) => Math.min(current, totalPages));
    }, [totalPages]);

    if (classes.length === 0) {
        return <p className={styles.emptyState}>No classes found.</p>;
    }

    return (
        <div className={styles.tableWrap}>
            <table className={styles.scheduleTable}>
                <colgroup>
                    <col className={styles.colCrn} />
                    <col className={styles.colCourse} />
                    <col className={styles.colInstructor} />
                    <col className={styles.colTas} />
                    <col className={styles.colRoom} />
                    <col className={styles.colEnrolled} />
                    <col className={styles.colDatetime} />
                    <col className={styles.colActions} />
                </colgroup>
                <thead>
                    <tr>
                        <th>CRN</th>
                        <th>Course</th>
                        <th>Instructor</th>
                        <th>TAs</th>
                        <th>Room</th>
                        <th>Enrolled</th>
                        <th>Date & Time</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {paginatedClasses.map((item) => (
                        <tr key={item.id}>
                            <td>{item.crn}</td>
                            <td>
                                <strong
                                    className={styles.cellEllipsis}
                                    title={item.course_number ?? undefined}>
                                    {item.course_number}
                                </strong>
                                <p
                                    className={styles.cellEllipsis}
                                    title={item.course_title ?? undefined}>
                                    {item.course_title}
                                </p>
                            </td>
                            <td>
                                <strong
                                    className={styles.cellEllipsis}
                                    title={item.instructor_name ?? undefined}>
                                    {item.instructor_name}
                                </strong>
                            </td>
                            <td>
                                <TaNamesCell taAssignments={item.ta_assignments} />
                            </td>
                            <td title={item.room_number ?? undefined}>{item.room_number}</td>
                            <td>{item.enrollment}</td>
                            <td>
                                <TimeDateCell meetings={item.meetings} />
                            </td>
                            <td>
                                <div className={styles.rowActions}>
                                    {onEdit ? (
                                        <button onClick={() => onEdit(String(item.id))} type="button">
                                            Edit
                                        </button>
                                    ) : null}
                                    <Link
                                        to={`./classes/${item.id}`}
                                        className="button-link"
                                        type="button">
                                        Edit
                                    </Link>
                                    <button
                                        className="button-danger"
                                        onClick={() =>
                                            onDelete(
                                                item.id,
                                                item.course_number +
                                                    ` (${item.course_title}, CRN: ${item.crn})`,
                                            )
                                        }
                                        type="button">
                                        Delete
                                    </button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <div className={styles.tablePagination}>
                <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} type="button">
                    Previous
                </button>
                <span>
                    Page {page} of {totalPages}
                </span>
                <button
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                    type="button">
                    Next
                </button>
            </div>
        </div>
    );
}
