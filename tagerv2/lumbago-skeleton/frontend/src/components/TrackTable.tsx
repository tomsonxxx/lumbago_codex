import React, { useState, useRef, useMemo } from "react";
import { AudioFile } from "../types";
import { StatusIcon } from "./StatusIcon";
import { SortConfig, SortKey } from "../utils/sortingUtils";

interface TrackTableProps {
  files: AudioFile[];
  selectedFileIds: string[];
  activeFileId: string | null;
  onSelect: (id: string, multi: boolean) => void;
  onSelectAll?: () => void;
  onActivate: (file: AudioFile) => void;
  sortConfig: SortConfig[];
  onSort: (config: SortConfig[]) => void;
  onContextMenu?: (e: React.MouseEvent, id: string) => void;

  // Pagination Props
  currentPage?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  itemsPerPage?: number;
  onItemsPerPageChange?: (items: number) => void;
}

interface ColumnDef {
  id: SortKey | "select";
  label: string;
  defaultWidth: number;
  minWidth: number;
  isSortable: boolean;
}

const columns: ColumnDef[] = [
  {
    id: "select",
    label: "",
    defaultWidth: 40,
    minWidth: 40,
    isSortable: false,
  },
  {
    id: "state",
    label: "Status",
    defaultWidth: 60,
    minWidth: 50,
    isSortable: true,
  },
  {
    id: "title",
    label: "Tytuł",
    defaultWidth: 220,
    minWidth: 150,
    isSortable: true,
  },
  {
    id: "artist",
    label: "Artysta",
    defaultWidth: 160,
    minWidth: 100,
    isSortable: true,
  },
  { id: "bpm", label: "BPM", defaultWidth: 60, minWidth: 50, isSortable: true },
  {
    id: "key",
    label: "Tonacja",
    defaultWidth: 70,
    minWidth: 60,
    isSortable: true,
  },
  {
    id: "genre",
    label: "Gatunek",
    defaultWidth: 120,
    minWidth: 80,
    isSortable: true,
  },
  {
    id: "rating",
    label: "Ocena",
    defaultWidth: 100,
    minWidth: 80,
    isSortable: true,
  },
  {
    id: "dateAdded",
    label: "Dodano",
    defaultWidth: 120,
    minWidth: 100,
    isSortable: true,
  },
];

const TrackTable: React.FC<TrackTableProps> = ({
  files,
  selectedFileIds,
  activeFileId,
  onSelect,
  onSelectAll,
  onActivate,
  sortConfig,
  onSort,
  onContextMenu,
  currentPage = 1,
  totalPages = 1,
  onPageChange,
  itemsPerPage = 50,
  onItemsPerPageChange,
}) => {
  // Column Resizing State
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>(() =>
    columns.reduce((acc, col) => ({ ...acc, [col.id]: col.defaultWidth }), {}),
  );
  const resizingRef = useRef<{
    id: string;
    startX: number;
    startWidth: number;
  } | null>(null);

  const allVisibleSelected = useMemo(
    () =>
      files.length > 0 && files.every((f) => selectedFileIds.includes(f.id)),
    [files, selectedFileIds],
  );
  const isIndeterminate = useMemo(
    () =>
      files.some((f) => selectedFileIds.includes(f.id)) && !allVisibleSelected,
    [files, selectedFileIds, allVisibleSelected],
  );

  // Sorting Handler
  const handleHeaderClick = (
    e: React.MouseEvent,
    key: string,
    isSortable: boolean,
  ) => {
    if (!isSortable) return;
    if ((e.target as HTMLElement).classList.contains("resizer")) return;

    const sortKey = key as SortKey;
    const existingIndex = sortConfig.findIndex((s) => s.key === sortKey);
    let newConfig = [...sortConfig];

    if (e.shiftKey) {
      if (existingIndex >= 0) {
        if (newConfig[existingIndex].direction === "asc") {
          newConfig[existingIndex].direction = "desc";
        } else {
          newConfig.splice(existingIndex, 1);
        }
      } else {
        newConfig.push({ key: sortKey, direction: "asc" });
      }
    } else {
      if (existingIndex >= 0 && sortConfig.length === 1) {
        newConfig = [
          {
            key: sortKey,
            direction:
              newConfig[existingIndex].direction === "asc" ? "desc" : "asc",
          },
        ];
      } else {
        newConfig = [{ key: sortKey, direction: "asc" }];
      }
    }
    onSort(newConfig);
  };

  // Resize Handlers
  const handleResizeStart = (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    resizingRef.current = {
      id,
      startX: e.clientX,
      startWidth: columnWidths[id],
    };
    document.body.style.cursor = "col-resize";
    document.addEventListener("mousemove", handleResizeMove);
    document.addEventListener("mouseup", handleResizeEnd);
  };

  const handleResizeMove = (e: MouseEvent) => {
    if (!resizingRef.current) return;
    const { id, startX, startWidth } = resizingRef.current;
    const diff = e.clientX - startX;
    const col = columns.find((c) => c.id === id);
    const minWidth = col ? col.minWidth : 50;

    setColumnWidths((prev) => ({
      ...prev,
      [id]: Math.max(minWidth, startWidth + diff),
    }));
  };

  const handleResizeEnd = () => {
    resizingRef.current = null;
    document.body.style.cursor = "";
    document.removeEventListener("mousemove", handleResizeMove);
    document.removeEventListener("mouseup", handleResizeEnd);
  };

  const handleRowClick = (e: React.MouseEvent, id: string) => {
    if ((e.target as HTMLElement).tagName === "INPUT") return;
    onSelect(id, e.ctrlKey || e.metaKey || e.shiftKey);
  };

  const renderStars = (rating: number | undefined) => {
    const stars = [];
    const val = rating || 0;
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span
          key={i}
          className={
            i <= val
              ? "text-yellow-400 drop-shadow-sm"
              : "text-slate-300 dark:text-slate-700"
          }
        >
          ★
        </span>,
      );
    }
    return <div className="text-xs tracking-tighter">{stars}</div>;
  };

  if (files.length === 0) {
    return null;
  }

  return (
    <div className="flex-grow flex flex-col overflow-hidden bg-white dark:bg-slate-950 select-none">
      <div className="flex-grow overflow-auto custom-scrollbar">
        <div style={{ minWidth: "100%", width: "fit-content" }}>
          {/* Header Row */}
          <div className="flex sticky top-0 bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 z-20 shadow-sm backdrop-blur-md bg-opacity-90 dark:bg-opacity-90">
            {columns.map((col) => {
              const sortIndex = sortConfig.findIndex((s) => s.key === col.id);
              const sortState = sortIndex >= 0 ? sortConfig[sortIndex] : null;

              return (
                <div
                  key={col.id}
                  className={`relative px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center group transition-colors ${!col.isSortable ? "cursor-default" : "cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800"}`}
                  style={{ width: columnWidths[col.id], flexShrink: 0 }}
                  onClick={(e) => handleHeaderClick(e, col.id, col.isSortable)}
                >
                  {col.id === "select" ? (
                    <div className="relative flex items-center justify-center w-4 h-4">
                      <input
                        type="checkbox"
                        checked={allVisibleSelected}
                        ref={(input) => {
                          if (input) input.indeterminate = isIndeterminate;
                        }}
                        onChange={() => onSelectAll && onSelectAll()}
                        className="peer appearance-none h-4 w-4 rounded border border-slate-300 dark:border-slate-600 bg-transparent checked:bg-indigo-600 checked:border-indigo-600 cursor-pointer transition-all"
                      />
                      <svg
                        className="absolute w-3 h-3 text-white pointer-events-none opacity-0 peer-checked:opacity-100 peer-indeterminate:opacity-100"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        {isIndeterminate ? (
                          <rect x="4" y="9" width="12" height="2" rx="1" />
                        ) : (
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        )}
                      </svg>
                    </div>
                  ) : (
                    <span
                      className={`truncate flex-grow ${sortState ? "text-indigo-600 dark:text-indigo-400" : ""}`}
                    >
                      {col.label}
                    </span>
                  )}

                  {sortState && (
                    <div className="flex items-center ml-1 text-indigo-600 dark:text-indigo-400">
                      {sortConfig.length > 1 && (
                        <span className="text-[9px] mr-0.5 font-bold bg-indigo-100 dark:bg-indigo-900/50 px-1 rounded">
                          {sortIndex + 1}
                        </span>
                      )}
                      {sortState.direction === "asc" ? (
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-3 w-3"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path
                            fillRule="evenodd"
                            d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                      ) : (
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-3 w-3"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path
                            fillRule="evenodd"
                            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                  )}

                  <div
                    className="resizer absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-indigo-500 z-30 opacity-0 group-hover:opacity-100"
                    onMouseDown={(e) => handleResizeStart(e, col.id)}
                  />
                </div>
              );
            })}
          </div>

          {/* Rows */}
          <div className="bg-white dark:bg-slate-900 pb-20">
            {files.map((file, index) => {
              const isSelected = selectedFileIds.includes(file.id);
              const isActive = activeFileId === file.id;
              const tags = file.fetchedTags || file.originalTags || {};
              const displayName = file.newName || file.file.name;
              const date = new Date(file.dateAdded).toLocaleDateString();

              return (
                <div
                  key={file.id}
                  onClick={(e) => handleRowClick(e, file.id)}
                  onDoubleClick={() => onActivate(file)}
                  onContextMenu={(e) =>
                    onContextMenu && onContextMenu(e, file.id)
                  }
                  className={`
                            flex items-center group cursor-pointer transition-all duration-150 text-sm relative
                            border-b border-slate-100 dark:border-slate-800/50
                            animate-fade-in
                            ${
                              isActive
                                ? "bg-indigo-50/90 dark:bg-indigo-900/40 z-10 shadow-[inset_2px_0_0_0_#6366f1]"
                                : isSelected
                                  ? "bg-indigo-50/50 dark:bg-indigo-900/20"
                                  : "hover:bg-slate-50 dark:hover:bg-slate-800/40 bg-white dark:bg-slate-900"
                            }
                        `}
                  style={{ animationDelay: `${Math.min(index * 20, 300)}ms` }}
                >
                  {/* Glowing effect for active item */}
                  {isActive && (
                    <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 to-transparent pointer-events-none" />
                  )}

                  <div
                    className="px-4 py-2 flex-shrink-0 flex items-center justify-center group/checkbox"
                    style={{ width: columnWidths["select"] }}
                  >
                    <div className="relative flex items-center justify-center w-4 h-4">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => onSelect(file.id, true)}
                        className={`
                                        peer appearance-none h-4 w-4 rounded border transition-all cursor-pointer z-10
                                        ${
                                          isSelected || isActive
                                            ? "bg-indigo-600 border-indigo-600"
                                            : "bg-transparent border-slate-300 dark:border-slate-600 group-hover/checkbox:border-indigo-400"
                                        }
                                    `}
                      />
                      <svg
                        className={`absolute w-3 h-3 text-white pointer-events-none transition-opacity duration-200 ${isSelected ? "opacity-100" : "opacity-0"}`}
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  </div>

                  <div
                    className="px-4 py-2 flex-shrink-0"
                    style={{ width: columnWidths["state"] }}
                  >
                    <div className="scale-75 origin-left transition-transform group-hover:scale-90">
                      <StatusIcon state={file.state} />
                    </div>
                  </div>
                  <div
                    className="px-4 py-2 flex-shrink-0 truncate"
                    style={{ width: columnWidths["title"] }}
                  >
                    <div className="flex flex-col truncate">
                      <span
                        className={`font-semibold truncate transition-colors ${isActive ? "text-indigo-600 dark:text-indigo-300" : "text-slate-700 dark:text-slate-200 group-hover:text-slate-900 dark:group-hover:text-white"}`}
                      >
                        {tags.title || displayName}
                      </span>
                    </div>
                  </div>
                  <div
                    className="px-4 py-2 flex-shrink-0 truncate text-slate-500 dark:text-slate-400 group-hover:text-slate-700 dark:group-hover:text-slate-300 transition-colors"
                    style={{ width: columnWidths["artist"] }}
                  >
                    {tags.artist || (
                      <span className="opacity-50 italic">Nieznany</span>
                    )}
                  </div>
                  <div
                    className="px-4 py-2 flex-shrink-0 truncate"
                    style={{ width: columnWidths["bpm"] }}
                  >
                    <span
                      className={`font-mono text-xs px-1.5 py-0.5 rounded ${isActive ? "bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 font-bold" : "text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800"}`}
                    >
                      {tags.bpm || "-"}
                    </span>
                  </div>
                  <div
                    className="px-4 py-2 flex-shrink-0 truncate"
                    style={{ width: columnWidths["key"] }}
                  >
                    <span
                      className={`font-mono text-xs px-1.5 py-0.5 rounded ${isActive ? "bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 font-bold" : "text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800"}`}
                    >
                      {tags.initialKey || "-"}
                    </span>
                  </div>
                  <div
                    className="px-4 py-2 flex-shrink-0 truncate text-slate-500 dark:text-slate-400"
                    style={{ width: columnWidths["genre"] }}
                  >
                    {tags.genre ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                        {tags.genre}
                      </span>
                    ) : (
                      "-"
                    )}
                  </div>
                  <div
                    className="px-4 py-2 flex-shrink-0"
                    style={{ width: columnWidths["rating"] }}
                  >
                    {renderStars(tags.rating)}
                  </div>
                  <div
                    className="px-4 py-2 flex-shrink-0 text-xs text-slate-400 dark:text-slate-500 font-mono"
                    style={{ width: columnWidths["dateAdded"] }}
                  >
                    {date}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-between px-4 py-2 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 text-xs backdrop-blur-sm sticky bottom-0 z-20">
          <div className="text-slate-500 dark:text-slate-400">
            Strona <strong>{currentPage}</strong> z{" "}
            <strong>{totalPages}</strong>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => onPageChange(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-2 py-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-50 transition-colors"
            >
              Poprzednia
            </button>
            <button
              onClick={() =>
                onPageChange(Math.min(totalPages, currentPage + 1))
              }
              disabled={currentPage === totalPages}
              className="px-2 py-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-50 transition-colors"
            >
              Następna
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrackTable;
