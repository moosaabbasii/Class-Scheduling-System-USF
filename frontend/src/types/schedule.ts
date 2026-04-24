export type ClassStatus = 'Scheduled' | 'Cancelled'

export type ScheduleFormValues = {
  courseCode: string
  courseTitle: string
  instructor: string
  ta: string
  room: string
  date: string
  startTime: string
  endTime: string
  status: ClassStatus
}

export type ClassScheduleItem = ScheduleFormValues & {
  id: string
}
