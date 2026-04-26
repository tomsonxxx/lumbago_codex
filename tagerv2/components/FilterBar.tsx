import React from "react";
import { LibraryFilters } from "../hooks/useLibrary";

interface FilterBarProps {
  filters: LibraryFilters;
  onFilterChange: (newFilters: LibraryFilters) => void;
  onClearFilters: () => void;
  availableGenres: string[];
}

const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onFilterChange,
  onClearFilters,
  availableGenres,
}) => {
  const handleChange = (key: keyof LibraryFilters, value: string | number) => {
    onFilterChange({ ...filters, [key]: value });
  };

  const hasActiveFilters =
    filters.bpmMin || filters.bpmMax || filters.genre || filters.key;

  return (
    <div className="bg-[var(--bg-surface)] dark:bg-[var(--bg-panel)] border-b border-[var(--border-color)] dark:border-[var(--border-color)] px-4 py-2 flex flex-wrap items-center gap-4 transition-all animate-fade-in">
      {/* BPM Filter */}
      <div className="flex items-center space-x-2">
        <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase">
          BPM
        </span>
        <div className="flex items-center bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] rounded-none border border-[var(--border-color)] dark:border-[var(--border-color)] overflow-hidden">
          <input
            type="number"
            placeholder="Min"
            className="w-14 p-1.5 text-xs bg-transparent text-center focus:outline-none text-[var(--text-primary)]"
            value={filters.bpmMin || ""}
            onChange={(e) =>
              handleChange(
                "bpmMin",
                e.target.value ? parseInt(e.target.value) : "",
              )
            }
          />
          <span className="text-[var(--text-secondary)]">-</span>
          <input
            type="number"
            placeholder="Max"
            className="w-14 p-1.5 text-xs bg-transparent text-center focus:outline-none text-[var(--text-primary)]"
            value={filters.bpmMax || ""}
            onChange={(e) =>
              handleChange(
                "bpmMax",
                e.target.value ? parseInt(e.target.value) : "",
              )
            }
          />
        </div>
      </div>

      {/* Genre Filter */}
      <div className="flex items-center space-x-2">
        <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase">
          Gatunek
        </span>
        <select
          className="bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] border border-[var(--border-color)] dark:border-[var(--border-color)] text-[var(--text-secondary)] dark:text-[var(--text-secondary)] text-xs rounded-none py-1.5 px-2 focus:outline-none focus:ring-1 focus:ring-[var(--accent-primary)]"
          value={filters.genre || ""}
          onChange={(e) => handleChange("genre", e.target.value)}
        >
          <option value="">Wszystkie</option>
          {availableGenres.map((g) => (
            <option key={g} value={g}>
              {g}
            </option>
          ))}
        </select>
      </div>

      {/* Key Filter */}
      <div className="flex items-center space-x-2">
        <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase">
          Klucz
        </span>
        <input
          type="text"
          placeholder="np. 11A"
          className="w-20 bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] border border-[var(--border-color)] dark:border-[var(--border-color)] text-[var(--text-secondary)] dark:text-[var(--text-secondary)] text-xs rounded-none py-1.5 px-2 focus:outline-none focus:ring-1 focus:ring-[var(--accent-primary)]"
          value={filters.key || ""}
          onChange={(e) => handleChange("key", e.target.value)}
        />
      </div>

      {/* Clear Button */}
      {hasActiveFilters && (
        <button
          onClick={onClearFilters}
          className="ml-auto text-xs text-red-500 hover:text-red-700 font-medium flex items-center"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-3 w-3 mr-1"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
          Wyczyść filtry
        </button>
      )}
    </div>
  );
};

export default FilterBar;
