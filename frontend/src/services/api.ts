export type ApiErrorResponse = {
    detail?: string;
};

export class ApiClientError extends Error {
    status: number;
    payload: unknown;

    constructor(message: string, status: number, payload: unknown) {
        super(message);
        this.name = 'ApiClientError';
        this.status = status;
        this.payload = payload;
    }
}

type RequestOptions = {
    body?: BodyInit;
    headers?: HeadersInit;
    method?: 'DELETE' | 'GET' | 'PATCH' | 'POST';
    query?: Record<string, boolean | number | string | undefined>;
};

export type User = {
    email: string;
    id: number;
    name: string;
    role: string;
};

export type Schedule = {
    approved_at: string | null;
    approved_by: number | null;
    created_at: string;
    created_by: number;
    id: number;
    locked: boolean;
    name: string;
    status: string;
};

export type AuditIssue = {
    audit_report_id: number;
    description: string;
    detected_at: string;
    id: number;
    resolved_at: string | null;
    section_id: number | null;
    status: 'open' | 'resolved';
    type: string;
};

export type AuditReport = {
    created_at: string;
    generated_by: number | null;
    generated_by_name: string | null;
    id: number;
    issues: AuditIssue[];
    passed: boolean;
    schedule_id: number;
    schedule_name: string | null;
    status: 'open' | 'cleared' | 'approved';
};

export type Meeting = {
    days: string;
    end_time: string;
    id: number;
    section_id: number;
    start_time: string;
};

export type TaAssignment = {
    assigned_hours: number;
    max_hours: number | null;
    ta_email: string | null;
    ta_id: number;
    ta_name: string | null;
};

export type TeachingAssistant = {
    email: string | null;
    hours: number;
    id: number;
    max_hours: number;
    name: string;
};

export type CourseSection = {
    catalog_course_id: number;
    course_number: string | null;
    course_title: string | null;
    crn: number;
    end_date: string | null;
    enrollment: number;
    id: number;
    instructor_email: string | null;
    instructor_id: number | null;
    instructor_name: string | null;
    level: string | null;
    meetings: Meeting[];
    room_id: number | null;
    room_number: string | null;
    schedule_id: number;
    start_date: string | null;
    ta_assignments: TaAssignment[];
};

export type CreateUserInput = {
    email: string;
    name: string;
    password: string;
    role: string;
};

export type CatalogCourseInput = {
    course_number: string;
    title: string;
};

export type CatalogCourse = {
    course_number: string;
    id: number;
    title: string;
};

export type RoomInput = {
    capacity: number;
    room_number: string;
};

export type Room = RoomInput & {
    id: number;
};

export type InstructorInput = {
    email: string;
    name: string;
};

export type TaInput = {
    email: string;
    max_hours: number;
    name: string;
};

export type CreateScheduleInput = {
    created_by: number;
    name: string;
    status: string;
};

export type CreateSectionInput = {
    catalog_course_id: number;
    crn?: number;
    end_date: string;
    enrollment?: number;
    instructor_id: number;
    level: string;
    meetings: Array<{
        days: string;
        end_time: string;
        start_time: string;
    }>;
    room_id: number;
    schedule_id?: number;
    start_date: string;
    ta_assignments: Array<{
        ta_id: number;
    }>;
};

export type EnrollmentComparisonParams = {
    actorUserId: number;
    courseNumber?: string;
    scheduleIds: number[];
    subject?: string;
};

export type ScheduleExportParams = {
    actorUserId: number;
    day?: string;
    instructorId?: number;
    roomId?: number;
    scheduleId: number;
};

export type AnalyticsExportParams = {
    actorUserId: number;
    courseNumber?: string;
    scheduleIds: number[];
    subject?: string;
};

function getErrorMessage(payload: unknown, fallback: string): string {
    if (
        typeof payload === 'object' &&
        payload !== null &&
        'detail' in payload &&
        typeof (payload as ApiErrorResponse).detail === 'string'
    ) {
        return (payload as ApiErrorResponse).detail as string;
    }

    return fallback;
}

function appendQueryParams(
    searchParams: URLSearchParams,
    query?: Record<string, boolean | number | string | undefined>,
) {
    if (!query) {
        return;
    }

    Object.entries(query).forEach(([key, value]) => {
        if (value === undefined || value === '') {
            return;
        }

        searchParams.set(key, String(value));
    });
}

async function parseResponse(response: Response): Promise<unknown> {
    if (response.status === 204) {
        return null;
    }

    const contentType = response.headers.get('content-type') ?? '';
    if (contentType.includes('application/json')) {
        return (await response.json()) as unknown;
    }

    if (contentType.includes('application/pdf')) {
        return await response.blob();
    }

    return await response.text();
}

export function createApiClient(baseUrl: string) {
    const normalizedBaseUrl = baseUrl.replace(/\/+$/, '');

    async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
        const url = new URL(`${normalizedBaseUrl}/api/v1${path}`);
        appendQueryParams(url.searchParams, options.query);

        const response = await fetch(url.toString(), {
            method: options.method ?? 'GET',
            headers: options.headers,
            body: options.body,
        });

        const payload = await parseResponse(response);

        if (!response.ok) {
            throw new ApiClientError(
                getErrorMessage(payload, `Request failed with HTTP ${response.status}.`),
                response.status,
                payload,
            );
        }

        return payload as T;
    }

    return {
        health: {
            check: () => request<{ status: string }>('/health'),
        },

        users: {
            create: (input: CreateUserInput) =>
                request<User>('/users', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(input),
                }),
            delete: (userId: number) =>
                request<null>(`/users/${userId}`, {
                    method: 'DELETE',
                }),
            getById: (userId: number) => request<User>(`/users/${userId}`),
            list: () => request<User[]>('/users'),
            update: (userId: number, input: Partial<CreateUserInput>) =>
                request<User>(`/users/${userId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(input),
                }),
        },

        lookups: {
            catalogCourses: {
                create: (input: CatalogCourseInput) =>
                    request('/catalog-courses', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(input),
                    }),
                delete: (itemId: number) =>
                    request(`/catalog-courses/${itemId}`, { method: 'DELETE' }),
                getById: (itemId: number) => `/catalog-courses/${itemId}`,
                list: () => request<CatalogCourse[]>('/catalog-courses'),
                update: (itemId: number, input: Partial<CatalogCourseInput>) =>
                    request(`/catalog-courses/${itemId}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(input),
                    }),
            },
            instructors: {
                create: (input: InstructorInput) =>
                    request('/instructors', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(input),
                    }),
                delete: (itemId: number) => request(`/instructors/${itemId}`, { method: 'DELETE' }),
                getById: (itemId: number) => request(`/instructors/${itemId}`),
                list: (params?: { limit?: number; query?: string }) =>
                    request('/instructors', {
                        query: {
                            query: params?.query,
                            limit: params?.limit,
                        },
                    }),
                update: (itemId: number, input: Partial<InstructorInput>) =>
                    request(`/instructors/${itemId}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(input),
                    }),
            },
            rooms: {
                create: (input: RoomInput) =>
                    request('/rooms', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(input),
                }),
                delete: (itemId: number) => request(`/rooms/${itemId}`, { method: 'DELETE' }),
                getById: (itemId: number) => request<Room>(`/rooms/${itemId}`),
                list: () => request<Room[]>('/rooms'),
                update: (itemId: number, input: Partial<RoomInput>) =>
                    request(`/rooms/${itemId}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(input),
                    }),
            },
            tas: {
                create: (input: TaInput) =>
                    request('/tas', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(input),
                    }),
                delete: (itemId: number) => request(`/tas/${itemId}`, { method: 'DELETE' }),
                getById: (itemId: number, scheduleId?: number) =>
                    request<TeachingAssistant>(`/tas/${itemId}`, {
                        query: { schedule_id: scheduleId },
                    }),
                list: (scheduleId?: number) =>
                    request<TeachingAssistant[]>('/tas', {
                        query: { schedule_id: scheduleId },
                    }),
                update: (itemId: number, input: Partial<TaInput>) =>
                    request<TeachingAssistant>(`/tas/${itemId}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(input),
                    }),
            },
        },

        schedules: {
            create: (actorUserId: number, input: CreateScheduleInput) =>
                request<Schedule>('/schedules', {
                    method: 'POST',
                    query: { actor_user_id: actorUserId },
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(input),
                }),
            delete: (scheduleId: number, actorUserId: number) =>
                request<null>(`/schedules/${scheduleId}`, {
                    method: 'DELETE',
                    query: { actor_user_id: actorUserId },
                }),
            finalize: (scheduleId: number, actorUserId: number) =>
                request<Schedule>(`/schedules/${scheduleId}/finalize`, {
                    method: 'POST',
                    query: { actor_user_id: actorUserId },
                }),
            getById: (scheduleId: number) => request<Schedule>(`/schedules/${scheduleId}`),
            list: () => request<Schedule[]>('/schedules'),
            listSections: (scheduleId: number) =>
                request<CourseSection[]>(`/schedules/${scheduleId}/sections`),
            lock: (scheduleId: number, actorUserId: number) =>
                request<Schedule>(`/schedules/${scheduleId}/lock`, {
                    method: 'POST',
                    query: { actor_user_id: actorUserId },
                }),
            unlock: (scheduleId: number, actorUserId: number) =>
                request<Schedule>(`/schedules/${scheduleId}/unlock`, {
                    method: 'POST',
                    query: { actor_user_id: actorUserId },
                }),
            update: (
                scheduleId: number,
                actorUserId: number,
                input: Partial<CreateScheduleInput>,
            ) =>
                request<Schedule>(`/schedules/${scheduleId}`, {
                    method: 'PATCH',
                    query: { actor_user_id: actorUserId },
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(input),
                }),
        },

        sections: {
            create: (scheduleId: number, actorUserId: number, input: CreateSectionInput) =>
                request<CourseSection>(`/schedules/${scheduleId}/sections`, {
                    method: 'POST',
                    query: { actor_user_id: actorUserId },
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(input),
                }),
            delete: (sectionId: number, actorUserId: number) =>
                request<null>(`/sections/${sectionId}`, {
                    method: 'DELETE',
                    query: { actor_user_id: actorUserId },
                }),
            getById: (sectionId: number) => request<CourseSection>(`/sections/${sectionId}`),
            update: (sectionId: number, actorUserId: number, input: Partial<CreateSectionInput>) =>
                request<CourseSection>(`/sections/${sectionId}`, {
                    method: 'PATCH',
                    query: { actor_user_id: actorUserId },
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(input),
                }),
        },

        audits: {
            getById: (reportId: number) => request<AuditReport>(`/audits/${reportId}`),
            list: (scheduleId?: number) =>
                request<AuditReport[]>('/audits', {
                    query: { schedule_id: scheduleId },
                }),
            runForSchedule: (scheduleId: number, actorUserId: number, generatedBy?: number) =>
                request<AuditReport>(`/audits/schedules/${scheduleId}`, {
                    method: 'POST',
                    query: { actor_user_id: actorUserId },
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(
                        generatedBy === undefined ? {} : { generated_by: generatedBy },
                    ),
                }),
            updateIssue: (issueId: number, input: Record<string, unknown>) =>
                request<AuditIssue>(`/audits/issues/${issueId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(input),
                }),
            updateReport: (reportId: number, input: Record<string, unknown>) =>
                request<AuditReport>(`/audits/${reportId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(input),
                }),
        },

        analytics: {
            enrollmentComparison: (params: EnrollmentComparisonParams) => {
                const url = new URL(`${normalizedBaseUrl}/api/v1/analytics/enrollment-comparison`);
                params.scheduleIds.forEach((scheduleId) => {
                    url.searchParams.append('schedule_ids', String(scheduleId));
                });
                appendQueryParams(url.searchParams, {
                    actor_user_id: params.actorUserId,
                    subject: params.subject,
                    course_number: params.courseNumber,
                });

                return fetch(url.toString()).then(async (response) => {
                    const payload = await parseResponse(response);
                    if (!response.ok) {
                        throw new ApiClientError(
                            getErrorMessage(
                                payload,
                                `Request failed with HTTP ${response.status}.`,
                            ),
                            response.status,
                            payload,
                        );
                    }

                    return payload;
                });
            },
        },

        exports: {
            analyticsComparisonPdf: (params: AnalyticsExportParams) => {
                const url = new URL(
                    `${normalizedBaseUrl}/api/v1/exports/analytics/enrollment-comparison/pdf`,
                );
                params.scheduleIds.forEach((scheduleId) => {
                    url.searchParams.append('schedule_ids', String(scheduleId));
                });
                appendQueryParams(url.searchParams, {
                    actor_user_id: params.actorUserId,
                    subject: params.subject,
                    course_number: params.courseNumber,
                });

                return fetch(url.toString()).then(async (response) => {
                    const payload = await parseResponse(response);
                    if (!response.ok) {
                        throw new ApiClientError(
                            getErrorMessage(
                                payload,
                                `Request failed with HTTP ${response.status}.`,
                            ),
                            response.status,
                            payload,
                        );
                    }

                    return payload as Blob;
                });
            },
            auditPdf: (reportId: number, actorUserId: number) =>
                request<Blob>(`/exports/audits/${reportId}/pdf`, {
                    query: { actor_user_id: actorUserId },
                }),
            schedulePdf: (params: ScheduleExportParams) =>
                request<Blob>('/exports/schedules/pdf', {
                    query: {
                        schedule_id: params.scheduleId,
                        actor_user_id: params.actorUserId,
                        day: params.day,
                        room_id: params.roomId,
                        instructor_id: params.instructorId,
                    },
                }),
            schedulePreview: (params: ScheduleExportParams) =>
                request('/exports/schedules/preview', {
                    query: {
                        schedule_id: params.scheduleId,
                        actor_user_id: params.actorUserId,
                        day: params.day,
                        room_id: params.roomId,
                        instructor_id: params.instructorId,
                    },
                }),
        },
    };
}
