import { useState, type ChangeEvent, type FormEvent } from 'react'
import type { ClassScheduleItem, ClassStatus, ScheduleFormValues } from '../types/schedule'

type ClassScheduleFormProps = {
  initialValues?: ClassScheduleItem | null
  mode: 'create' | 'edit'
  onCancel: () => void
  onSubmit: (values: ScheduleFormValues) => void
}

const defaultValues: ScheduleFormValues = {
  courseCode: '',
  courseTitle: '',
  instructor: '',
  ta: '',
  room: '',
  date: '',
  startTime: '',
  endTime: '',
  status: 'Scheduled',
}

export function ClassScheduleForm({
  initialValues,
  mode,
  onCancel,
  onSubmit,
}: ClassScheduleFormProps) {
  const [formValues, setFormValues] = useState<ScheduleFormValues>(
    initialValues
      ? {
          courseCode: initialValues.courseCode,
          courseTitle: initialValues.courseTitle,
          instructor: initialValues.instructor,
          ta: initialValues.ta,
          room: initialValues.room,
          date: initialValues.date,
          startTime: initialValues.startTime,
          endTime: initialValues.endTime,
          status: initialValues.status,
        }
      : defaultValues,
  )

  const handleChange =
    (field: keyof ScheduleFormValues) =>
    (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const value =
        field === 'status'
          ? (event.target.value as ClassStatus)
          : event.target.value
      setFormValues((previous) => ({
        ...previous,
        [field]: value,
      }))
    }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit(formValues)
    if (mode === 'create') {
      setFormValues(defaultValues)
    }
  }

  return (
    <form className="schedule-form" onSubmit={handleSubmit}>
      <label>
        Course Code
        <input
          onChange={handleChange('courseCode')}
          required
          type="text"
          value={formValues.courseCode}
        />
      </label>

      <label>
        Course Title
        <input
          onChange={handleChange('courseTitle')}
          required
          type="text"
          value={formValues.courseTitle}
        />
      </label>

      <label>
        Instructor
        <input
          onChange={handleChange('instructor')}
          required
          type="text"
          value={formValues.instructor}
        />
      </label>

      <label>
        Teaching Assistant
        <input
          onChange={handleChange('ta')}
          required
          type="text"
          value={formValues.ta}
        />
      </label>

      <label>
        Room
        <input
          onChange={handleChange('room')}
          required
          type="text"
          value={formValues.room}
        />
      </label>

      <label>
        Date
        <input
          onChange={handleChange('date')}
          required
          type="date"
          value={formValues.date}
        />
      </label>

      <label>
        Start Time
        <input
          onChange={handleChange('startTime')}
          required
          type="time"
          value={formValues.startTime}
        />
      </label>

      <label>
        End Time
        <input
          onChange={handleChange('endTime')}
          required
          type="time"
          value={formValues.endTime}
        />
      </label>

      <label>
        Status
        <select onChange={handleChange('status')} value={formValues.status}>
          <option value="Scheduled">Scheduled</option>
          <option value="Cancelled">Cancelled</option>
        </select>
      </label>

      <div className="actions">
        <button type="submit">{mode === 'edit' ? 'Save Changes' : 'Add Class'}</button>
        {mode === 'edit' ? (
          <button className="button-secondary" onClick={onCancel} type="button">
            Cancel Edit
          </button>
        ) : null}
      </div>
    </form>
  )
}
