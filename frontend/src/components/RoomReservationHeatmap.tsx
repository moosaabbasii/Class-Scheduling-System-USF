import { useMemo, useState } from 'react';
import type { CSSProperties } from 'react';
import type { CourseSection, Room } from '../services/api';
import styles from './RoomReservationHeatmap.module.css';

const DAY_COLUMNS = [
    { key: 'M', label: 'Mon' },
    { key: 'T', label: 'Tue' },
    { key: 'W', label: 'Wed' },
    { key: 'R', label: 'Thu' },
    { key: 'F', label: 'Fri' },
] as const;

const SLOT_MINUTES = 30;
const DEFAULT_START_MINUTES = 8 * 60;
const DEFAULT_END_MINUTES = 18 * 60;
const ALL_ROOMS_VALUE = '__all_rooms__';

type RoomReservationHeatmapProps = {
    classes: CourseSection[];
    rooms: Room[];
};

type AggregatedRoom = {
    id: number;
    roomNumber: string;
    capacity: number | null;
    reservationCount: number;
    reservedMinutes: number;
    utilizationPercent: number;
};

type GridSection = {
    courseNumber: string;
    crn: number;
    roomNumber: string;
};

function parseTimeToMinutes(value: string) {
    const [hours, minutes] = value.split(':').map((part) => Number.parseInt(part, 10));
    if (!Number.isFinite(hours) || !Number.isFinite(minutes)) {
        return null;
    }

    return hours * 60 + minutes;
}

function floorToSlot(value: number) {
    return Math.floor(value / SLOT_MINUTES) * SLOT_MINUTES;
}

function ceilToSlot(value: number) {
    return Math.ceil(value / SLOT_MINUTES) * SLOT_MINUTES;
}

function formatTimeLabel(minutes: number) {
    const hours = Math.floor(minutes / 60);
    const remainder = minutes % 60;
    const suffix = hours >= 12 ? 'PM' : 'AM';
    const hour12 = hours % 12 === 0 ? 12 : hours % 12;
    return `${hour12}:${String(remainder).padStart(2, '0')} ${suffix}`;
}

function formatHours(minutes: number) {
    return `${Math.round((minutes / 60) * 10) / 10} hrs`;
}

function sortRooms(left: AggregatedRoom, right: AggregatedRoom) {
    if (left.utilizationPercent !== right.utilizationPercent) {
        return left.utilizationPercent - right.utilizationPercent;
    }

    if (left.reservedMinutes !== right.reservedMinutes) {
        return left.reservedMinutes - right.reservedMinutes;
    }

    return left.roomNumber.localeCompare(right.roomNumber, undefined, { numeric: true });
}

export function RoomReservationHeatmap({ classes, rooms }: RoomReservationHeatmapProps) {
    const [selectedRoomId, setSelectedRoomId] = useState(ALL_ROOMS_VALUE);
    const [viewMode, setViewMode] = useState<'heatmap' | 'table'>('heatmap');

    const {
        allRooms,
        filteredRooms,
        gridScheduleByDay,
        maxConcurrentReservations,
        roomsWithNoReservations,
        timeSlots,
        utilizationBaselineMinutes,
    } = useMemo(() => {
        const allMeetingMinutes = classes.flatMap((section) =>
            section.meetings.flatMap((meeting) => {
                const start = parseTimeToMinutes(meeting.start_time);
                const end = parseTimeToMinutes(meeting.end_time);

                if (start === null || end === null || end <= start) {
                    return [];
                }

                return [start, end];
            }),
        );

        const minMinutes = allMeetingMinutes.length
            ? floorToSlot(Math.min(...allMeetingMinutes))
            : DEFAULT_START_MINUTES;
        const maxMinutes = allMeetingMinutes.length
            ? ceilToSlot(Math.max(...allMeetingMinutes))
            : DEFAULT_END_MINUTES;
        const boundedEndMinutes = Math.max(maxMinutes, minMinutes + SLOT_MINUTES);

        const allRoomsMap = new Map<number, AggregatedRoom>();
        rooms.forEach((room) => {
            allRoomsMap.set(room.id, {
                id: room.id,
                roomNumber: room.room_number,
                capacity: room.capacity ?? null,
                reservationCount: 0,
                reservedMinutes: 0,
                utilizationPercent: 0,
            });
        });

        classes.forEach((section) => {
            if (section.room_id === null) {
                return;
            }

            const room = allRoomsMap.get(section.room_id);
            if (!room) {
                return;
            }

            section.meetings.forEach((meeting) => {
                const start = parseTimeToMinutes(meeting.start_time);
                const end = parseTimeToMinutes(meeting.end_time);
                if (start === null || end === null || end <= start) {
                    return;
                }

                const durationMinutes = end - start;
                const seenDays = new Set<string>();
                Array.from(meeting.days.toUpperCase()).forEach((dayKey) => {
                    if (!DAY_COLUMNS.some((day) => day.key === dayKey) || seenDays.has(dayKey)) {
                        return;
                    }

                    seenDays.add(dayKey);
                    room.reservedMinutes += durationMinutes;
                });

                room.reservationCount += 1;
            });
        });

        const nextTimeSlots = [];
        for (let minutes = minMinutes; minutes < boundedEndMinutes; minutes += SLOT_MINUTES) {
            nextTimeSlots.push(minutes);
        }

        const baselineMinutes = nextTimeSlots.length * SLOT_MINUTES * DAY_COLUMNS.length;
        allRoomsMap.forEach((room) => {
            room.utilizationPercent =
                baselineMinutes === 0
                    ? 0
                    : Math.round((room.reservedMinutes / baselineMinutes) * 100);
        });

        const nextAllRooms = Array.from(allRoomsMap.values()).sort(sortRooms);
        const nextFilteredRooms =
            selectedRoomId === ALL_ROOMS_VALUE
                ? nextAllRooms
                : nextAllRooms.filter((room) => String(room.id) === selectedRoomId);

        const nextGridScheduleByDay = new Map<string, Map<number, GridSection[]>>();
        let peakReservations = 1;
        classes.forEach((section) => {
            if (section.room_id === null || section.room_number === null) {
                return;
            }

            if (
                selectedRoomId !== ALL_ROOMS_VALUE &&
                String(section.room_id) !== selectedRoomId
            ) {
                return;
            }

            section.meetings.forEach((meeting) => {
                const start = parseTimeToMinutes(meeting.start_time);
                const end = parseTimeToMinutes(meeting.end_time);
                if (start === null || end === null || end <= start) {
                    return;
                }

                const entry: GridSection = {
                    courseNumber: section.course_number ?? 'Course',
                    crn: section.crn,
                    roomNumber: section.room_number ?? `Room ${section.room_id}`,
                };

                const seenDays = new Set<string>();
                Array.from(meeting.days.toUpperCase()).forEach((dayKey) => {
                    if (!DAY_COLUMNS.some((day) => day.key === dayKey) || seenDays.has(dayKey)) {
                        return;
                    }

                    seenDays.add(dayKey);
                    const slotsForDay =
                        nextGridScheduleByDay.get(dayKey) ?? new Map<number, GridSection[]>();

                    for (
                        let slotStart = floorToSlot(start);
                        slotStart < end;
                        slotStart += SLOT_MINUTES
                    ) {
                        const items = slotsForDay.get(slotStart) ?? [];
                        items.push(entry);
                        slotsForDay.set(slotStart, items);
                        peakReservations = Math.max(peakReservations, items.length);
                    }

                    nextGridScheduleByDay.set(dayKey, slotsForDay);
                });
            });
        });

        const zeroReservationRooms = nextAllRooms.filter((room) => room.reservedMinutes === 0).length;

        return {
            allRooms: nextAllRooms,
            filteredRooms: nextFilteredRooms,
            gridScheduleByDay: nextGridScheduleByDay,
            maxConcurrentReservations: peakReservations,
            roomsWithNoReservations: zeroReservationRooms,
            timeSlots: nextTimeSlots,
            utilizationBaselineMinutes: baselineMinutes,
        };
    }, [classes, rooms, selectedRoomId]);

    const selectedRoom =
        selectedRoomId === ALL_ROOMS_VALUE
            ? null
            : allRooms.find((room) => String(room.id) === selectedRoomId) ?? null;

    if (allRooms.length === 0) {
        return <p className={styles.emptyState}>No rooms are available for this schedule.</p>;
    }

    return (
        <div className={styles.wrapper}>
            <div className={styles.summaryRow}>
                <article className={styles.summaryCard}>
                    <span className={styles.summaryLabel}>Rooms tracked</span>
                    <strong>{allRooms.length}</strong>
                    <p>Includes rooms with zero reservations so unused space stays visible.</p>
                </article>
                <article className={styles.summaryCard}>
                    <span className={styles.summaryLabel}>Underused now</span>
                    <strong>{roomsWithNoReservations}</strong>
                    <p>Rooms with no scheduled reservations across the displayed weekly grid.</p>
                </article>
                <article className={styles.summaryCard}>
                    <span className={styles.summaryLabel}>Weekly baseline</span>
                    <strong>{Math.round(utilizationBaselineMinutes / 60)} hrs</strong>
                    <p>Shared weekday timetable used to measure room utilization.</p>
                </article>
            </div>

            <div className={styles.controlsRow}>
                <div className={styles.viewSwitcher}>
                    <button
                        className={viewMode === 'heatmap' ? styles.activeViewButton : undefined}
                        onClick={() => setViewMode('heatmap')}
                        type="button">
                        Heat Map
                    </button>
                    <button
                        className={viewMode === 'table' ? styles.activeViewButton : undefined}
                        onClick={() => setViewMode('table')}
                        type="button">
                        Table
                    </button>
                </div>
                <label className={styles.selectorLabel}>
                    Room filter
                    <select
                        onChange={(event) => setSelectedRoomId(event.target.value)}
                        value={selectedRoomId}>
                        <option value={ALL_ROOMS_VALUE}>All rooms</option>
                        {allRooms.map((room) => (
                            <option key={room.id} value={room.id}>
                                {room.roomNumber}
                            </option>
                        ))}
                    </select>
                </label>
            </div>

            {viewMode === 'table' ? (
                <div className={styles.tableWrap}>
                    <table className={styles.roomTable}>
                        <thead>
                            <tr>
                                <th>Room</th>
                                <th>Capacity</th>
                                <th>Reservations</th>
                                <th>Reserved Time</th>
                                <th>Utilization</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredRooms.map((room) => (
                                <tr key={room.id}>
                                    <td>{room.roomNumber}</td>
                                    <td>{room.capacity ?? 'Not set'}</td>
                                    <td>{room.reservationCount}</td>
                                    <td>{formatHours(room.reservedMinutes)}</td>
                                    <td>{room.utilizationPercent}%</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <section className={styles.detailCard}>
                    <div className={styles.detailHeader}>
                        <div>
                            <h3>{selectedRoom ? selectedRoom.roomNumber : 'All rooms'}</h3>
                            <p>
                                {selectedRoom
                                    ? selectedRoom.capacity
                                        ? `Capacity ${selectedRoom.capacity}`
                                        : 'Capacity not set'
                                    : 'Combined reservation load across every room in the schedule'}
                            </p>
                        </div>
                        <div className={styles.roomMetrics}>
                            <strong>
                                {selectedRoom
                                    ? `${selectedRoom.utilizationPercent}% utilized`
                                    : `${filteredRooms.reduce((sum, room) => sum + room.reservationCount, 0)} reservations`}
                            </strong>
                            <span>
                                {selectedRoom
                                    ? `${formatHours(selectedRoom.reservedMinutes)} reserved`
                                    : `${formatHours(
                                          filteredRooms.reduce(
                                              (sum, room) => sum + room.reservedMinutes,
                                              0,
                                          ),
                                      )} reserved across all rooms`}
                            </span>
                        </div>
                    </div>

                    <div className={styles.legend}>
                        <span className={styles.legendSwatchEmpty} />
                        <span>Available</span>
                        <span className={styles.legendSwatchReserved} />
                        <span>Reserved</span>
                    </div>

                    <div className={styles.gridWrap}>
                        <div className={styles.grid}>
                            <div className={styles.cornerCell}>Time</div>
                            {DAY_COLUMNS.map((day) => (
                                <div className={styles.dayHeader} key={day.key}>
                                    {day.label}
                                </div>
                            ))}
                            {timeSlots.map((slotStart) => (
                                <div className={styles.gridRow} key={`${selectedRoomId}-${slotStart}`}>
                                    <div className={styles.timeCell}>{formatTimeLabel(slotStart)}</div>
                                    {DAY_COLUMNS.map((day) => {
                                        const sections =
                                            gridScheduleByDay.get(day.key)?.get(slotStart) ?? [];
                                        const intensity =
                                            sections.length === 0
                                                ? 0
                                                : Math.max(
                                                      0.2,
                                                      sections.length / maxConcurrentReservations,
                                                  );
                                        const title =
                                            sections.length === 0
                                                ? `${selectedRoom ? selectedRoom.roomNumber : 'All rooms'} open on ${day.label} at ${formatTimeLabel(slotStart)}`
                                                : `${selectedRoom ? selectedRoom.roomNumber : 'All rooms'} reserved on ${day.label} at ${formatTimeLabel(slotStart)}: ${sections
                                                      .map(
                                                          (section) =>
                                                              `${section.courseNumber} CRN ${section.crn} in ${section.roomNumber}`,
                                                      )
                                                      .join(', ')}`;

                                        return (
                                            <div
                                                className={styles.slotCell}
                                                key={`${selectedRoomId}-${day.key}-${slotStart}`}
                                                style={
                                                    {
                                                        '--heat-intensity': intensity,
                                                    } as CSSProperties
                                                }
                                                title={title}>
                                                {sections.length > 0 ? (
                                                    <span className={styles.slotCount}>
                                                        {sections.length}
                                                    </span>
                                                ) : null}
                                            </div>
                                        );
                                    })}
                                </div>
                            ))}
                        </div>
                    </div>
                </section>
            )}
        </div>
    );
}
