import { useMemo, useState, type ChangeEvent, type FormEvent } from 'react';
import type { CreateClassFormValues } from '../types/createClass';
import { Combobox } from './Combobox';
import styles from './CreateClassForm.module.css';

type InstructorOption = {
    id: number;
    name: string;
};

type CourseOption = {
    id: number;
    label: string;
    name: string;
};

type TaOption = {
    email?: string | null;
    hours?: number;
    id: number;
    maxHours: number;
    name: string;
};

type CreateClassFormProps = {
    courses: CourseOption[];
    courseSearch: string;
    instructors: InstructorOption[];
    instructorSearch: string;
    isLoadingCourses?: boolean;
    isLoadingInstructors?: boolean;
    isLoadingTas?: boolean;
    isSubmitting: boolean;
    onReset: () => void;
    onCourseIdChange: (id: string) => void;
    onCourseSearchChange: (value: string) => void;
    onInstructorIdChange: (id: string) => void;
    onInstructorSearchChange: (value: string) => void;
    onMeetingDaysChange: (value: string) => void;
    onChange: (
        field: keyof CreateClassFormValues,
    ) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
    onSubmit: (event: FormEvent<HTMLFormElement>) => void;
    onTaAssignmentAdd: (taId: string) => void;
    onTaMaxHoursSave: (taId: number, maxHours: number) => Promise<string | null>;
    onTaAssignmentRemove: (index: number) => void;
    tas: TaOption[];
    values: CreateClassFormValues;
};

type SectionDataProps = {
    courseSearch: string;
    courses: CourseOption[];
    instructors: InstructorOption[];
    instructorSearch: string;
    isLoadingCourses: boolean;
    isLoadingInstructors: boolean;
    onChange: (
        field: keyof CreateClassFormValues,
    ) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
    onCourseIdChange: (id: string) => void;
    onCourseSearchChange: (value: string) => void;
    onInstructorIdChange: (id: string) => void;
    onInstructorSearchChange: (value: string) => void;
    onMeetingDaysChange: (value: string) => void;
    values: CreateClassFormValues;
};

const DAY_ORDER = ['M', 'T', 'W', 'R', 'F'] as const;

function normalizeMeetingDays(value: string): string {
    const enabledDays = new Set(
        Array.from(value.toUpperCase()).filter((character) =>
            DAY_ORDER.includes(character as (typeof DAY_ORDER)[number]),
        ),
    );

    return DAY_ORDER.filter((day) => enabledDays.has(day)).join('');
}

function SectionData({
    courseSearch,
    courses,
    instructors,
    instructorSearch,
    isLoadingCourses,
    isLoadingInstructors,
    onChange,
    onCourseIdChange,
    onCourseSearchChange,
    onInstructorIdChange,
    onInstructorSearchChange,
    onMeetingDaysChange,
    values,
}: SectionDataProps) {
    const toggleMeetingDay = (day: (typeof DAY_ORDER)[number]) => {
        const enabledDays = new Set(Array.from(values.meetingDays));

        if (enabledDays.has(day)) {
            enabledDays.delete(day);
        } else {
            enabledDays.add(day);
        }

        onMeetingDaysChange(normalizeMeetingDays(Array.from(enabledDays).join('')));
    };

    return (
        <div className={styles.sectionData}>
            <label>
                Level*
                <select onChange={onChange('level')} value={values.level}>
                    <option value="UG">UG</option>
                    <option value="GR">GR</option>
                </select>
            </label>

            <label>
                Course*
                <Combobox
                    values={courses}
                    isLoading={isLoadingCourses}
                    onOptionIdChange={onCourseIdChange}
                    onSearchChange={onCourseSearchChange}
                    selectedOptionId={values.catalogCourseId}
                    searchValue={courseSearch}
                    placeholder="Type course number or title"
                    required
                />
            </label>

            <label>
                Start Date*
                <input
                    onChange={onChange('startDate')}
                    required
                    type="date"
                    value={values.startDate}
                />
            </label>

            <label>
                End Date*
                <input onChange={onChange('endDate')} required type="date" value={values.endDate} />
            </label>

            <label>
                Room ID*
                <input
                    min="1"
                    onChange={onChange('roomId')}
                    required
                    type="number"
                    value={values.roomId}
                />
            </label>

            <label>
                Instructor*
                <Combobox
                    values={instructors}
                    isLoading={isLoadingInstructors}
                    onOptionIdChange={onInstructorIdChange}
                    onSearchChange={onInstructorSearchChange}
                    selectedOptionId={values.instructorId}
                    searchValue={instructorSearch}
                    required
                />
            </label>
            <label>
                Meeting Start
                <input
                    onChange={onChange('meetingStart')}
                    type="time"
                    value={values.meetingStart}
                />
            </label>

            <label>
                Meeting End
                <input
                    onChange={onChange('meetingEnd')}
                    type="time"
                    value={values.meetingEnd}
                />
            </label>

            <label>
                Meeting Days
                <div className={styles.meetingDaysInput}>
                    {DAY_ORDER.map((day) => (
                        <button
                            key={day}
                            className={values.meetingDays.includes(day) ? styles.dayActive : ''}
                            onClick={() => toggleMeetingDay(day)}
                            type="button">
                            {day}
                        </button>
                    ))}
                </div>
            </label>
        </div>
    );
}

type TaAssignmentsProps = {
    isLoadingTas: boolean;
    isSubmitting: boolean;
    onTaAssignmentAdd: (taId: string) => void;
    onTaMaxHoursSave: (taId: number, maxHours: number) => Promise<string | null>;
    onTaAssignmentRemove: (index: number) => void;
    tas: TaOption[];
    values: CreateClassFormValues;
};

function TaAssignments({
    isLoadingTas,
    isSubmitting,
    onTaAssignmentAdd,
    onTaMaxHoursSave,
    onTaAssignmentRemove,
    tas,
    values,
}: TaAssignmentsProps) {
    const [taSearch, setTaSearch] = useState('');
    const [selectedTaId, setSelectedTaId] = useState('');
    const [addError, setAddError] = useState<string | null>(null);
    const [draftMaxHours, setDraftMaxHours] = useState<Record<string, string>>({});
    const [saveMessages, setSaveMessages] = useState<Record<string, string | null>>({});
    const [savingTaId, setSavingTaId] = useState<string | null>(null);
    const taById = useMemo(() => new Map(tas.map((ta) => [String(ta.id), ta])), [tas]);

    const getDraftMaxHours = (taId: string, currentMaxHours?: number) =>
        draftMaxHours[taId] ?? String(currentMaxHours ?? 0);

    const handleAddTa = () => {
        const normalizedTaId = selectedTaId.trim();

        if (!normalizedTaId) {
            setAddError('Select a TA before adding.');
            return;
        }

        if (values.taAssignments.some((assignment) => assignment.taId === normalizedTaId)) {
            setAddError('This TA is already assigned to the class.');
            return;
        }

        onTaAssignmentAdd(normalizedTaId);
        setSelectedTaId('');
        setTaSearch('');
        setAddError(null);
    };

    const handleSaveMaxHours = async (taId: string, currentMaxHours?: number) => {
        const parsedTaId = Number.parseInt(taId, 10);
        if (!Number.isFinite(parsedTaId)) {
            setSaveMessages((previous) => ({
                ...previous,
                [taId]: 'Invalid TA id.',
            }));
            return;
        }

        const nextMaxHours = Number.parseInt(getDraftMaxHours(taId, currentMaxHours), 10);
        if (!Number.isFinite(nextMaxHours) || nextMaxHours < 0) {
            setSaveMessages((previous) => ({
                ...previous,
                [taId]: 'Max hours must be a non-negative integer.',
            }));
            return;
        }

        setSavingTaId(taId);
        const errorMessage = await onTaMaxHoursSave(parsedTaId, nextMaxHours);
        setSaveMessages((previous) => ({
            ...previous,
            [taId]: errorMessage ?? 'Saved.',
        }));
        setDraftMaxHours((previous) => ({
            ...previous,
            [taId]: String(nextMaxHours),
        }));
        setSavingTaId(null);
    };

    return (
        <div className={styles.taTable}>
            <h2>TA Assignments</h2>
            <div className={styles.taAssignmentControls}>
                <label className={styles.taSelectLabel}>
                    Select TA
                    <Combobox
                        values={tas}
                        isLoading={isLoadingTas}
                        onOptionIdChange={setSelectedTaId}
                        onSearchChange={setTaSearch}
                        selectedOptionId={selectedTaId}
                        searchValue={taSearch}
                    />
                </label>
                <button disabled={isSubmitting} onClick={handleAddTa} type="button">
                    Add TA
                </button>
            </div>
            {addError ? <p className="form-message is-error">{addError}</p> : null}
            <table>
                <thead>
                    <tr>
                        <th>TA</th>
                        <th>Email</th>
                        <th>Weekly Hours</th>
                        <th>Max Hours</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {values.taAssignments.length === 0 ? (
                        <tr>
                            <td colSpan={5}>No TAs assigned yet.</td>
                        </tr>
                    ) : (
                        values.taAssignments.map((assignment, index) => {
                            const ta = taById.get(assignment.taId);
                            const isSaving = savingTaId === assignment.taId;
                            return (
                                <tr key={`${assignment.taId}-${index}`}>
                                    <td>
                                        {ta
                                            ? `${ta.name} (ID: ${ta.id})`
                                            : `TA #${assignment.taId}`}
                                    </td>
                                    <td>{ta?.email ?? '-'}</td>
                                    <td>{ta?.hours ?? '-'}</td>
                                    <td>
                                        <input
                                            disabled={isSaving}
                                            min="0"
                                            onChange={(event) => {
                                                setDraftMaxHours((previous) => ({
                                                    ...previous,
                                                    [assignment.taId]: event.target.value,
                                                }));
                                                setSaveMessages((previous) => ({
                                                    ...previous,
                                                    [assignment.taId]: null,
                                                }));
                                            }}
                                            type="number"
                                            value={getDraftMaxHours(assignment.taId, ta?.maxHours)}
                                        />
                                    </td>
                                    <td>
                                        <div className="row-actions">
                                            <button
                                                disabled={isSaving}
                                                onClick={() =>
                                                    handleSaveMaxHours(
                                                        assignment.taId,
                                                        ta?.maxHours,
                                                    )
                                                }
                                                type="button">
                                                {isSaving ? 'Saving...' : 'Save'}
                                            </button>
                                            <button
                                                className="button-danger"
                                                onClick={() => onTaAssignmentRemove(index)}
                                                type="button">
                                                Remove
                                            </button>
                                            {saveMessages[assignment.taId] ? (
                                                <span
                                                    className={
                                                        saveMessages[assignment.taId] === 'Saved.'
                                                            ? 'inline-message is-success'
                                                            : 'inline-message is-error'
                                                    }>
                                                    {saveMessages[assignment.taId]}
                                                </span>
                                            ) : null}
                                        </div>
                                    </td>
                                </tr>
                            );
                        })
                    )}
                </tbody>
            </table>
        </div>
    );
}

export function CreateClassForm({
    courses,
    courseSearch,
    instructors,
    instructorSearch,
    isLoadingCourses = false,
    isLoadingInstructors = false,
    isLoadingTas = false,
    isSubmitting,
    onReset,
    onCourseIdChange,
    onCourseSearchChange,
    onInstructorIdChange,
    onInstructorSearchChange,
    onMeetingDaysChange,
    onChange,
    onSubmit,
    onTaAssignmentAdd,
    onTaMaxHoursSave,
    onTaAssignmentRemove,
    tas,
    values,
}: CreateClassFormProps) {
    const [selectedSubSection, setSelectedSubSection] = useState<'section' | 'tas'>('section');

    return (
        <>
            <div className={styles.tabControls}>
                <label className={styles.tabLabel}>
                    <input
                        className={styles.radioInput}
                        checked={selectedSubSection === 'section'}
                        name="class-form-subtabs"
                        onChange={() => setSelectedSubSection('section')}
                        type="radio"
                    />
                    <span className={styles.tabText}>Section Details</span>
                </label>
                <label className={styles.tabLabel}>
                    <input
                        className={styles.radioInput}
                        checked={selectedSubSection === 'tas'}
                        name="class-form-subtabs"
                        onChange={() => setSelectedSubSection('tas')}
                        type="radio"
                    />
                    <span className={styles.tabText}>TA Assignments</span>
                </label>
            </div>

            <form className={`${styles.scheduleForm} panel`} onSubmit={onSubmit}>
                {selectedSubSection === 'section' ? (
                    <SectionData
                        courseSearch={courseSearch}
                        courses={courses}
                        instructors={instructors}
                        instructorSearch={instructorSearch}
                        isLoadingCourses={isLoadingCourses}
                        isLoadingInstructors={isLoadingInstructors}
                        onChange={onChange}
                        onCourseIdChange={onCourseIdChange}
                        onCourseSearchChange={onCourseSearchChange}
                        onInstructorIdChange={onInstructorIdChange}
                        onInstructorSearchChange={onInstructorSearchChange}
                        onMeetingDaysChange={onMeetingDaysChange}
                        values={values}
                    />
                ) : (
                    <TaAssignments
                        isLoadingTas={isLoadingTas}
                        isSubmitting={isSubmitting}
                        onTaAssignmentAdd={onTaAssignmentAdd}
                        onTaMaxHoursSave={onTaMaxHoursSave}
                        onTaAssignmentRemove={onTaAssignmentRemove}
                        tas={tas}
                        values={values}
                    />
                )}

                <div className="actions">
                    <button disabled={isSubmitting} type="submit">
                        {isSubmitting ? 'Applying...' : 'Apply'}
                    </button>
                    <button
                        className="button-danger"
                        disabled={isSubmitting}
                        onClick={onReset}
                        type="button">
                        {'Reset'}
                    </button>
                </div>
            </form>
        </>
    );
}
