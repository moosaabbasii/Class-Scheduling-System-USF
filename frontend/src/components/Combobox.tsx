import { useMemo, useState, type ChangeEvent } from 'react';
import styles from './Combobox.module.css';

export type ComboboxOption = {
    id: number;
    label?: string;
    name: string;
    email?: string | null;
};

type ComboboxProps = {
    values: ComboboxOption[];
    isLoading?: boolean;
    onOptionIdChange: (id: string) => void;
    onSearchChange: (searchValue: string) => void;
    selectedOptionId: string;
    searchValue: string;
    placeholder?: string;
    required?: boolean;
};

export function Combobox({
    values,
    isLoading = false,
    onOptionIdChange,
    onSearchChange,
    selectedOptionId,
    searchValue,
    placeholder = 'Type name or email',
    required = false,
}: ComboboxProps) {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const options = useMemo(
        () =>
            values.map((person) => ({
                id: person.id,
                label: person.label ?? `${person.name} (ID: ${person.id})`,
            })),
        [values],
    );
    const filteredOptions = useMemo(() => {
        const query = searchValue.trim().toLocaleLowerCase();
        if (!query) {
            return options;
        }

        return options.filter((option) => option.label.toLocaleLowerCase().includes(query));
    }, [options, searchValue]);

    const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
        onSearchChange(event.target.value);
        onOptionIdChange('');
        setIsMenuOpen(true);
    };

    const handleSelect = (id: number, label: string) => {
        onSearchChange(label);
        onOptionIdChange(String(id));
        setIsMenuOpen(false);
    };

    return (
        <div className={styles.combobox}>
            <input
                autoComplete="off"
                onBlur={() => {
                    window.setTimeout(() => setIsMenuOpen(false), 120);
                }}
                onChange={handleInputChange}
                onFocus={() => setIsMenuOpen(true)}
                placeholder={isLoading ? 'Loading values...' : placeholder}
                required={required}
                type="search"
                value={searchValue}
            />
            <input readOnly required={required} tabIndex={-1} type="hidden" value={selectedOptionId} />
            {isMenuOpen && filteredOptions.length > 0 ? (
                <ul className={styles.menu} role="listbox">
                    {filteredOptions.map((option) => (
                        <li key={option.id} role="option">
                            <button
                                className={styles.optionButton}
                                onClick={() => handleSelect(option.id, option.label)}
                                type="button"
                            >
                                {option.label}
                            </button>
                        </li>
                    ))}
                </ul>
            ) : null}
        </div>
    );
}
