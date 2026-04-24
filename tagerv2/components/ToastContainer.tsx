import React, { useEffect } from "react";

export type ToastType = "success" | "error" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastContainerProps {
  toasts: Toast[];
  removeToast: (id: string) => void;
}

const ToastItem: React.FC<{ toast: Toast; onRemove: (id: string) => void }> = ({
  toast,
  onRemove,
}) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(toast.id);
    }, 5000); // Auto dismiss after 5 seconds
    return () => clearTimeout(timer);
  }, [toast.id, onRemove]);

  let bgClass = "";
  let icon = null;

  switch (toast.type) {
    case "success":
      bgClass =
        "bg-green-50 dark:bg-green-900/90 border-green-200 dark:border-green-800 text-green-800 dark:text-green-100";
      icon = (
        <svg
          className="w-5 h-5 mr-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M5 13l4 4L19 7"
          />
        </svg>
      );
      break;
    case "error":
      bgClass =
        "bg-red-50 dark:bg-red-900/90 border-red-200 dark:border-red-800 text-red-800 dark:text-red-100";
      icon = (
        <svg
          className="w-5 h-5 mr-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      );
      break;
    default:
      bgClass =
        "bg-[var(--accent-secondary)] dark:bg-[var(--accent-secondary)] border-indigo-200 dark:border-indigo-800 text-[var(--accent-primary)] dark:text-[var(--accent-primary)]";
      icon = (
        <svg
          className="w-5 h-5 mr-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      );
  }

  return (
    <div
      className={`flex items-center p-4 mb-3 rounded-none border shadow-lg backdrop-blur-md animate-slide-in-right ${bgClass} min-w-[320px] max-w-md pointer-events-auto`}
    >
      {icon}
      <div className="flex-1 text-sm font-medium">{toast.message}</div>
      <button
        onClick={() => onRemove(toast.id)}
        className="ml-4 opacity-70 hover:opacity-100 focus:outline-none transition-opacity"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
};

const ToastContainer: React.FC<ToastContainerProps> = ({
  toasts,
  removeToast,
}) => {
  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col items-end pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
      ))}
    </div>
  );
};

export default ToastContainer;
