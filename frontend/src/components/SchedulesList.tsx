import styles from './SchedulesList.module.css';
import type { Schedule } from '../services/api';
import { Link } from 'react-router-dom';

type ScheduleShortCardProps = {
    schedule: Schedule;
};

type SchedulesListProps = {
    schedules: Schedule[];
};

function ScheduleShortCard({ schedule }: ScheduleShortCardProps) {
    return (
        <Link className={styles.card} to={`/schedules/${schedule.id}`} relative="path">
            <div className={styles.cardHead}>
                <h2>{schedule.name}</h2>
                <span className={styles.status}>{schedule.status}</span>
            </div>
            <p>Created by user {schedule.created_by}</p>
            <p>{schedule.locked ? 'Locked' : 'Open for edits'}</p>
        </Link>
    );
}

export default function SchedulesList({ schedules }: SchedulesListProps) {
    return (
        <section className={styles.container}>
            {schedules.map((schedule) => (
                <ScheduleShortCard key={schedule.id} schedule={schedule} />
            ))}
        </section>
    );
}
