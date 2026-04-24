export type TaAssignmentFormValues = {
    taId: string;
};

export type CreateClassFormValues = {
    scheduleId: string;
    catalogCourseId: string;
    level: 'UG' | 'GR';
    startDate: string;
    endDate: string;
    roomId: string;
    instructorId: string;
    meetingDays: string;
    meetingStart: string;
    meetingEnd: string;
    taAssignments: TaAssignmentFormValues[];
};

export const defaultCreateClassFormValues: CreateClassFormValues = {
    scheduleId: '',
    catalogCourseId: '',
    level: 'UG',
    startDate: '',
    endDate: '',
    roomId: '',
    instructorId: '',
    meetingDays: '',
    meetingStart: '',
    meetingEnd: '',
    taAssignments: [],
};
