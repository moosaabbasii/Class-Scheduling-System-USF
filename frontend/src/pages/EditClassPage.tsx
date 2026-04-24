import { CreateClassForm } from '../components/CreateClassForm';
import { useApiClient } from '../services/useApiClient';
import { useEffect, useState, type ChangeEvent, type FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import {
    defaultCreateClassFormValues,
    type CreateClassFormValues,
    type TaAssignmentFormValues,
} from '../types/createClass';
import { PageHeader } from '../components/PageHeader';
import {
    ApiClientError,
    type CatalogCourse,
    type CourseSection,
    type TeachingAssistant,
} from '../services/api';
import { useCurrentUser } from '../services/useCurrentUser';

function parseInteger(value: string): number {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : 0;
}

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

function toFormValues(section: CourseSection, scheduleIdFromRoute: string): CreateClassFormValues {
    const firstMeeting = section.meetings[0];
    const parsedScheduleId = Number.parseInt(scheduleIdFromRoute, 10);

    return {
        scheduleId: Number.isFinite(parsedScheduleId)
            ? String(parsedScheduleId)
            : String(section.schedule_id),
        catalogCourseId: String(section.catalog_course_id),
        level: section.level === 'GR' ? 'GR' : 'UG',
        startDate: section.start_date ?? '',
        endDate: section.end_date ?? '',
        roomId: section.room_id === null ? '' : String(section.room_id),
        instructorId: section.instructor_id === null ? '' : String(section.instructor_id),
        meetingDays: firstMeeting?.days ?? '',
        meetingStart: firstMeeting?.start_time ?? '',
        meetingEnd: firstMeeting?.end_time ?? '',
        taAssignments:
            section.ta_assignments.length > 0
                ? section.ta_assignments.map((assignment) => ({
                      taId: String(assignment.ta_id),
                  }))
                : [],
    };
}

export default function EditClassPage() {
    const api = useApiClient();
    const { currentUserId } = useCurrentUser();
    const { classId, scheduleId } = useParams();
    const [values, setValues] = useState<CreateClassFormValues>(defaultCreateClassFormValues);
    const [initialValues, setInitialValues] = useState<CreateClassFormValues>(
        defaultCreateClassFormValues,
    );
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isLoadingClass, setIsLoadingClass] = useState(true);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [courses, setCourses] = useState<CatalogCourse[]>([]);
    const [courseSearch, setCourseSearch] = useState('');
    const [isLoadingCourses, setIsLoadingCourses] = useState(true);
    const [instructors, setInstructors] = useState<Array<{ id: number; name: string }>>([]);
    const [instructorSearch, setInstructorSearch] = useState('');
    const [isLoadingInstructors, setIsLoadingInstructors] = useState(true);
    const [tas, setTas] = useState<TeachingAssistant[]>([]);
    const [isLoadingTas, setIsLoadingTas] = useState(true);

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
                })) as Array<{ id: number; name: string }>;
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
                const currentScheduleId = parseInteger(values.scheduleId);
                const response = await api.lookups.tas.list(
                    currentScheduleId > 0 ? currentScheduleId : undefined,
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

    useEffect(() => {
        const parsedClassId = Number.parseInt(classId ?? '', 10);
        if (!Number.isFinite(parsedClassId)) {
            setError('Invalid class id in route.');
            setIsLoadingClass(false);
            return;
        }

        const fetchSection = async () => {
            setIsLoadingClass(true);
            setError(null);

            try {
                const section = await api.sections.getById(parsedClassId);
                const nextValues = toFormValues(section, scheduleId ?? '');
                setValues(nextValues);
                setInitialValues(nextValues);
                const selectedCourse = courses.find(
                    (course) => course.id === section.catalog_course_id,
                );
                setCourseSearch(
                    selectedCourse
                        ? `${selectedCourse.course_number} - ${selectedCourse.title}`
                        : section.course_number && section.course_title
                          ? `${section.course_number} - ${section.course_title}`
                          : '',
                );
                if (section.instructor_name && section.instructor_id !== null) {
                    setInstructorSearch(
                        `${section.instructor_name} (ID: ${section.instructor_id})`,
                    );
                } else {
                    setInstructorSearch('');
                }
            } catch (caughtError) {
                if (caughtError instanceof ApiClientError) {
                    setError(caughtError.message);
                    return;
                }
                setError('Unable to load class details.');
            } finally {
                setIsLoadingClass(false);
            }
        };

        fetchSection();
    }, [api, classId, courses, scheduleId]);

    const handleChange =
        (field: keyof CreateClassFormValues) =>
        (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
            setValues((previous) => ({
                ...previous,
                [field]: event.target.value,
            }));
        };

    const handleReset = () => {
        setValues(initialValues);
        const selectedCourse = courses.find(
            (course) => String(course.id) === initialValues.catalogCourseId,
        );
        setCourseSearch(
            selectedCourse
                ? `${selectedCourse.course_number} - ${selectedCourse.title}`
                : '',
        );
        const selectedInstructor = instructors.find(
            (instructor) => String(instructor.id) === initialValues.instructorId,
        );
        setInstructorSearch(
            selectedInstructor
                ? `${selectedInstructor.name} (ID: ${selectedInstructor.id})`
                : '',
        );
        setMessage(null);
        setError(null);
    };

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setError(null);
        setMessage(null);

        setIsSubmitting(true);

        try {
            const sectionId = Number.parseInt(classId ?? '', 10);
            if (!Number.isFinite(sectionId)) {
                throw new Error('Invalid class id in route.');
            }

            const taAssignments = toTaAssignments(values.taAssignments);
            const section = await api.sections.update(sectionId, currentUserId, {
                schedule_id: parseInteger(values.scheduleId),
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
                    ? `Class section updated successfully. Section ID: ${section.id}.`
                    : 'Class section updated successfully.',
            );
            const nextValues = toFormValues(section, scheduleId ?? '');
            setValues(nextValues);
            setInitialValues(nextValues);
            if (section.course_number && section.course_title) {
                setCourseSearch(`${section.course_number} - ${section.course_title}`);
            }
            if (section.instructor_name && section.instructor_id !== null) {
                setInstructorSearch(`${section.instructor_name} (ID: ${section.instructor_id})`);
            }
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
                title={courseSearch || 'Edit Class'}
                eyebrow="Edit Class"
                subtitle={
                    isLoadingClass ? 'Loading class details...' : 'Edit an existing class'
                }
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
