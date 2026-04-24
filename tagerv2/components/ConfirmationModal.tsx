import React from "react";

interface ConfirmationModalProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  title: string;
  children: React.ReactNode;
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onConfirm,
  onCancel,
  title,
  children,
}) => {
  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 bg-black/80 backdrop-blur-md flex justify-center items-center z-50 animate-fade-in"
      onClick={onCancel}
    >
      <div
        className="glass-panel w-full max-w-md mx-4 p-8 rounded-[2.5rem] border border-white/10 shadow-2xl relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--accent-magenta)]/10 blur-3xl rounded-full -mr-16 -mt-16"></div>
        
        <h2 className="text-2xl font-bold text-white font-heading mb-4 relative z-10">
          {title}
        </h2>
        <div className="text-white/60 text-sm leading-relaxed mb-8 relative z-10">
          {children}
        </div>
        
        <div className="flex justify-between items-center relative z-10">
          <button
            onClick={onCancel}
            className="px-6 py-2 text-xs font-bold text-white/30 hover:text-white uppercase tracking-widest transition-colors"
          >
            Anuluj
          </button>
          <button
            onClick={onConfirm}
            className="px-8 py-4 bg-[var(--accent-magenta)] text-white text-xs font-bold rounded-2xl glow-magenta hover:scale-105 active:scale-95 transition-all uppercase tracking-widest"
          >
            Potwierdź
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;
