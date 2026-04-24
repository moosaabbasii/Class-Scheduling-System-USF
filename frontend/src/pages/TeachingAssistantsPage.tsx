import { useEffect, useMemo, useState } from 'react';
import { PageHeader } from '../components/PageHeader';
import { ApiClientError, type TeachingAssistant } from '../services/api';
import { useApiClient } from '../services/useApiClient';

type DraftHoursState = Record<number, string>;
type RowState = Record<number, string | null>;

function parseNonNegativeInteger(value: string): number {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
}

export default function TeachingAssistantsPage() {
    const api = useApiClient();
    const [tas, setTas] = useState<TeachingAssistant[]>([]);
    const [draftHours, setDraftHours] = useState<DraftHoursState>({});
    const [isLoading, setIsLoading] = useState(true);
    const [savingId, setSavingId] = useState<number | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [rowMessages, setRowMessages] = useState<RowState>({});
    const [query, setQuery] = useState('');

    useEffect(() => {
        let isMounted = true;

        async function loadTas() {
            setIsLoading(true);
            setError(null);

            try {
                const response = await api.lookups.tas.list();
                if (!isMounted) {
                    return;
                }
                setTas(response);
                setDraftHours(
                    Object.fromEntries(response.map((ta) => [ta.id, String(ta.max_hours)])),
                );
            } catch (caughtError) {
                if (!isMounted) {
                    return;
                }
                if (caughtError instanceof ApiClientError) {
                    setError(caughtError.message);
                } else {
                    setError('Unable to load TAs. Verify the backend is running.');
                }
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        }

        loadTas();
        return () => {
            isMounted = false;
        };
    }, [api]);

    const filteredTas = useMemo(() => {
        const normalizedQuery = query.trim().toLowerCase();
        if (!normalizedQuery) {
            return tas;
        }
        return tas.filter((ta) => {
            return (
                ta.name.toLowerCase().includes(normalizedQuery) ||
                ta.email?.toLowerCase().includes(normalizedQuery) ||
                String(ta.id).includes(normalizedQuery)
            );
        });
    }, [query, tas]);

    const updateDraft = (id: number, value: string) => {
        setDraftHours((previous) => ({
            ...previous,
            [id]: value,
        }));
        setRowMessages((previous) => ({
            ...previous,
            [id]: null,
        }));
    };

    const handleSave = async (ta: TeachingAssistant) => {
        const nextValue = draftHours[ta.id] ?? String(ta.max_hours);
        const nextHours = parseNonNegativeInteger(nextValue);

        setSavingId(ta.id);
        setRowMessages((previous) => ({
            ...previous,
            [ta.id]: null,
        }));

        try {
            const updated = await api.lookups.tas.update(ta.id, { max_hours: nextHours });
            setTas((previous) =>
                previous.map((item) => (item.id === ta.id ? { ...item, ...updated } : item)),
            );
            setDraftHours((previous) => ({
                ...previous,
                [ta.id]: String(updated.max_hours),
            }));
            setRowMessages((previous) => ({
                ...previous,
                [ta.id]: 'Saved.',
            }));
        } catch (caughtError) {
            const message =
                caughtError instanceof ApiClientError
                    ? caughtError.message
                    : 'Unable to update max hours.';
            setRowMessages((previous) => ({
                ...previous,
                [ta.id]: message,
            }));
        } finally {
            setSavingId(null);
        }
    };

    return (
        <div className="app-shell">
            <PageHeader
                eyebrow="TA Directory"
                title="Teaching Assistants"
                subtitle="Update each TA's max weekly hours. Derived hours remain schedule-specific."
            />

            <section className="panel">
                <div className="panel-head">
                    <h2>TA Limits</h2>
                    <div className="panel-actions">
                        <input
                            aria-label="Search TAs"
                            className="search-input"
                            onChange={(event) => setQuery(event.target.value)}
                            placeholder="Search by name, email, or ID..."
                            type="search"
                            value={query}
                        />
                    </div>
                </div>

                {isLoading ? <p>Loading TAs...</p> : null}
                {error ? <p className="form-message is-error">{error}</p> : null}

                {!isLoading && !error ? (
                    <div className="table-wrap">
                        <table className="simple-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>Email</th>
                                    <th>Max Hours</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredTas.length === 0 ? (
                                    <tr>
                                        <td colSpan={5}>No TAs found.</td>
                                    </tr>
                                ) : (
                                    filteredTas.map((ta) => {
                                        const draftValue = draftHours[ta.id] ?? String(ta.max_hours);
                                        const isSaving = savingId === ta.id;
                                        return (
                                            <tr key={ta.id}>
                                                <td>{ta.id}</td>
                                                <td>{ta.name}</td>
                                                <td>{ta.email ?? '-'}</td>
                                                <td>
                                                    <input
                                                        min="0"
                                                        onChange={(event) =>
                                                            updateDraft(ta.id, event.target.value)
                                                        }
                                                        type="number"
                                                        value={draftValue}
                                                    />
                                                </td>
                                                <td>
                                                    <div className="row-actions compact-row-actions">
                                                        <button
                                                            disabled={isSaving}
                                                            onClick={() => handleSave(ta)}
                                                            type="button">
                                                            {isSaving ? 'Saving...' : 'Save'}
                                                        </button>
                                                        {rowMessages[ta.id] ? (
                                                            <span
                                                                className={
                                                                    rowMessages[ta.id] === 'Saved.'
                                                                        ? 'inline-message is-success'
                                                                        : 'inline-message is-error'
                                                                }>
                                                                {rowMessages[ta.id]}
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
                ) : null}
            </section>
        </div>
    );
}
