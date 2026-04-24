import { CreateClassForm } from '../components/CreateClassForm';
import { useEffect, useState, type ChangeEvent, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
    ApiClientError,
    type CatalogCourse,
    type TeachingAssistant,
} from '../services/api';
import { useApiClient } from '../services/useApiClient';
import { useCurrentUser } from '../services/useCurrentUser';
import { PageHeader } from '../components/PageHeader';
import {
    defaultCreateClassFormValues,
    type CreateClassFormValues,
    type TaAssignmentFormValues,
} from '../types/createClass';

function parseInteger(value: string): number {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : 0;
}

type InstructorOption = {
    id: number;
    name: string;
};

function toTaAssignments(assignments: TaAssignmentFormValues[]): { ta_id: number }[] {
    const parsedAssignments: { ta_id: number }[] = [];

    for (const assignment of assignments) {
        const taId = assignment.taId.trim();

        if (!taId) {
            continue;
        }

        parsedAssignments.push({
            ta_id: parseInteger(taId),
        });
    }

    return parsedAssignments;
}

function toMeetings(values: CreateClassFormValues) {
    const days = values.meetingDays.trim();
    const startTime = values.meetingStart.trim();
    const endTime = values.meetingEnd.trim();

    if (!days && !startTime && !endTime) {
        return [];
    }

    return [
        {
            days,
            start_time: startTime,
            end_time: endTime,
        },
    ];
}

export default function CreateClassPage() {
    const api = useApiClient();
    const navigate = useNavigate();
    const { currentUserId } = useCurrentUser();
    const { scheduleId: scheduleIdFromRoute } = useParams();
    const [values, setValues] = useState<CreateClassFormValues>(
        defaultCreateClassFormValues,
    );
    const [courses, setCourses] = useState<CatalogCourse[]>([]);
    const [courseSearch, setCourseSearch] = useState('');
    const [isLoadingCourses, setIsLoadingCourses] = useState(true);
    const [instructors, setInstructors] = useState<InstructorOption[]>([]);
    const [instructorSearch, setInstructorSearch] = useState('');
    const [isLoadingInstructors, setIsLoadingInstructors] = useState(true);
    const [tas, setTas] = useState<TeachingAssistant[]>([]);
    const [isLoadingTas, setIsLoadingTas] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const parsedScheduleId = parseInteger(scheduleIdFromRoute ?? '');
        if (parsedScheduleId > 0) {
            setValues((previous) =>
                previous.scheduleId === String(parsedScheduleId)
                    ? previous
                    : { ...previous, scheduleId: String(parsedScheduleId) },
            );
        }
    }, [scheduleIdFromRoute]);

    useEffect(() => {
        const fetchCourses = async () => {
            setIsLoadingCourses(true);
            try {
                const response = await api.lookups.catalogCourses.list();
                setCourses(response);
            } catch {
                setCourses([]);
            } finally {
                setIsLoadingCourses(false);
            }
        };

        fetchCourses();
    }, [api]);

    useEffect(() => {
        const fetchInstructors = async () => {
            setIsLoadingInstructors(true);
            try {
                const response = (await api.lookups.instructors.list({
                    limit: 20,
                    query: instructorSearch.trim(),
                })) as InstructorOption[];
                setInstructors(response);
            } catch {
                setInstructors([]);
            } finally {
                setIsLoadingInstructors(false);
            }
        };

        const timeoutId = window.setTimeout(fetchInstructors, 300);
        return () => window.clearTimeout(timeoutId);
    }, [api, instructorSearch]);

    useEffect(() => {
        const fetchTas = async () => {
            setIsLoadingTas(true);
            try {
                const scheduleId = parseInteger(values.scheduleId);
                const response = await api.lookups.tas.list(
                    scheduleId > 0 ? scheduleId : undefined,
                );
                setTas(response);
            } catch {
                setTas([]);
            } finally {
                setIsLoadingTas(false);
            }
        };

        fetchTas();
    }, [api, values.scheduleId]);

    const handleChange =
        (field: keyof CreateClassFormValues) =>
        (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
            setValues((previous) => ({
                ...previous,
                [field]: event.target.value,
            }));
        };

    const handleReset = () => {
        setValues({
            ...defaultCreateClassFormValues,
            scheduleId: values.scheduleId,
        });
        setCourseSearch('');
        setInstructorSearch('');
        setMessage(null);
        setError(null);
    };

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setError(null);
        setMessage(null);

        setIsSubmitting(true);

        try {
            const taAssignments = toTaAssignments(values.taAssignments);
            const scheduleId = parseInteger(values.scheduleId);
            const section = await api.sections.create(scheduleId, currentUserId, {
                catalog_course_id: parseInteger(values.catalogCourseId),
                level: values.level,
                start_date: values.startDate,
                end_date: values.endDate,
                room_id: parseInteger(values.roomId),
                instructor_id: parseInteger(values.instructorId),
                meetings: toMeetings(values),
                ta_assignments: taAssignments,
            });

            setMessage(
                section.id
                    ? `Class section created successfully. Section ID: ${section.id}.`
                    : 'Class section created successfully.',
            );
            
            navigate('..', {relative: 'path'});
        } catch (caughtError) {
            if (caughtError instanceof ApiClientError) {
                setError(caughtError.message);
                return;
            }
            if (caughtError instanceof Error) {
                setError(caughtError.message);
                return;
            }

            setError('Unable to reach API. Verify backend is running and base URL is correct.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleTaMaxHoursSave = async (taId: number, maxHours: number) => {
        try {
            const updated = await api.lookups.tas.update(taId, { max_hours: maxHours });
            setTas((previous) =>
                previous.map((item) => (item.id === taId ? updated : item)),
            );
            return null;
        } catch (caughtError) {
            if (caughtError instanceof ApiClientError) {
                return caughtError.message;
            }
            return 'Unable to update max hours.';
        }
    };

    return (
        <div className="app-shell">
            <PageHeader
                title={courseSearch || 'Create Class'}
                eyebrow="Create Class"
                subtitle="Create a new class"
            />

            <CreateClassForm
                courses={courses.map((course) => ({
                    id: course.id,
                    label: `${course.course_number} - ${course.title}`,
                    name: course.course_number,
                }))}
                courseSearch={courseSearch}
                isLoadingCourses={isLoadingCourses}
                isSubmitting={isSubmitting}
                isLoadingTas={isLoadingTas}
                onReset={handleReset}
                onCourseSearchChange={setCourseSearch}
                onCourseIdChange={(id) =>
                    setValues((previous) => ({ ...previous, catalogCourseId: id }))
                }
                onMeetingDaysChange={(value) =>
                    setValues((previous) => ({ ...previous, meetingDays: value }))
                }
                onChange={handleChange}
                onSubmit={handleSubmit}
                onTaAssignmentAdd={(taId) =>
                    setValues((previous) => ({
                        ...previous,
                        taAssignments: [...previous.taAssignments, { taId }],
                    }))
                }
                onTaMaxHoursSave={handleTaMaxHoursSave}
                onTaAssignmentRemove={(index) =>
                    setValues((previous) => ({
                        ...previous,
                        taAssignments: previous.taAssignments.filter(
                            (_item, itemIndex) => itemIndex !== index,
                        ),
                    }))
                }
                values={values}
                instructors={instructors}
                instructorSearch={instructorSearch}
                isLoadingInstructors={isLoadingInstructors}
                onInstructorSearchChange={setInstructorSearch}
                onInstructorIdChange={(id) =>
                    setValues((previous) => ({ ...previous, instructorId: id }))
                }
                tas={tas.map((ta) => ({
                    email: ta.email,
                    hours: ta.hours,
                    id: ta.id,
                    maxHours: ta.max_hours,
                    name: ta.name,
                }))}
            />
            {message ? <p className="form-message is-success">{message}</p> : null}
            {error ? <p className="form-message is-error">{error}</p> : null}
        </div>
    );
}
