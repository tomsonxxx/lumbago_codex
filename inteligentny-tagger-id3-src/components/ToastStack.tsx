import React from 'react';

export interface ToastItem {
  id: string;
  type: 'success' | 'error' | 'info';
  title: string;
  message: string;
}

const toneMap: Record<ToastItem['type'], string> = {
  success: 'border-emerald-300 bg-emerald-50 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-200',
  error: 'border-fuchsia-300 bg-fuchsia-50 text-fuchsia-900 dark:border-fuchsia-800 dark:bg-fuchsia-900/20 dark:text-fuchsia-200',
  info: 'border-cyan-300 bg-cyan-50 text-cyan-900 dark:border-cyan-800 dark:bg-cyan-900/20 dark:text-cyan-200',
};

const ToastStack: React.FC<{ items: ToastItem[]; onDismiss: (id: string) => void }> = ({ items, onDismiss }) => {
  return (
    <div className="pointer-events-none fixed right-4 top-4 z-[100] flex w-[360px] max-w-[calc(100vw-2rem)] flex-col gap-2">
      {items.map((item) => (
        <div key={item.id} className={`pointer-events-auto rounded-lg border p-3 shadow-lg ${toneMap[item.type]}`}>
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-sm font-bold">{item.title}</p>
              <p className="mt-1 text-xs opacity-90">{item.message}</p>
            </div>
            <button
              onClick={() => onDismiss(item.id)}
              className="rounded p-1 text-xs opacity-70 transition-opacity hover:opacity-100"
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ToastStack;

