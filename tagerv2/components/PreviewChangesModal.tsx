import React from "react";

interface PreviewItem {
  originalName: string;
  newName: string;
  isTooLong: boolean;
}

interface PreviewChangesModalProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  title: string;
  previews: PreviewItem[];
  children: React.ReactNode;
}

const PreviewChangesModal: React.FC<PreviewChangesModalProps> = ({
  isOpen,
  onConfirm,
  onCancel,
  title,
  previews,
  children,
}) => {
  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 bg-black/80 backdrop-blur-sm flex justify-center items-center z-50"
      aria-modal="true"
      role="dialog"
      onClick={onCancel}
    >
      <div
        className="glass-panel w-full max-w-2xl mx-4 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h2>{title}</h2>
        <div className="font-mono text-[10px] text-[var(--text-muted)] mb-4 tracking-widest uppercase">
          {children}
        </div>

        <div className="tech-panel p-3 max-h-64 overflow-y-auto mt-4 bg-black">
          <p className="text-[10px] font-mono font-bold text-[var(--text-primary)] sticky top-0 bg-black pb-2 border-b border-[#333]">
            OPERATION_PREVIEW [{previews.length} FILES]:
          </p>
          <ul className="text-[10px] font-mono mt-3 space-y-2">
            {previews.map((previewItem, index) => (
              <li
                key={index}
                className="grid grid-cols-[1fr,auto,1fr] gap-2 items-center"
              >
                <span
                  className="truncate text-[var(--text-muted)] text-right"
                  title={previewItem.originalName}
                >
                  {previewItem.originalName}
                </span>
                <span className="text-[var(--border-color)]">=&gt;</span>
                <span
                  className={`flex items-center truncate ${previewItem.isTooLong ? "text-[#ff4500]" : "text-[var(--text-primary)]"}`}
                  title={previewItem.newName}
                >
                  {previewItem.isTooLong && (
                    <span
                      className="font-bold mr-1"
                      title="Path exceeds 255 chars"
                    >
                      [!]
                    </span>
                  )}
                  <span className="truncate">{previewItem.newName}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex justify-end space-x-2 mt-6 pt-4 border-t border-[#333]">
          <button
            onClick={onCancel}
            className="tech-button bg-black hover:bg-[#222]"
          >
            ABORT
          </button>
          <button
            onClick={onConfirm}
            className="tech-button bg-[var(--accent-secondary)]/20 border-[var(--accent-secondary)] text-white"
          >
            CONFIRM_EXECUTION
          </button>
        </div>
      </div>
      <style>{`
        @keyframes fade-in-scale {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        .animate-fade-in-scale { animation: fade-in-scale 0.2s ease-out forwards; }
      `}</style>
    </div>
  );
};

export default PreviewChangesModal;
