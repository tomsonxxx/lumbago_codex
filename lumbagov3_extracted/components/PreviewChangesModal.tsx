import React from 'react';

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
      className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50 transition-opacity duration-300"
      aria-modal="true"
      role="dialog"
      onClick={onCancel}
    >
      <div
        className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-2xl mx-4 transform transition-all duration-300 scale-95 opacity-0 animate-fade-in-scale"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">{title}</h2>
        <div className="text-slate-600 dark:text-slate-300 mb-4">{children}</div>

        <div className="mt-4 p-3 bg-slate-100 dark:bg-slate-900 rounded-md max-h-64 overflow-y-auto">
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 sticky top-0 bg-slate-100 dark:bg-slate-900 pb-2">
            Podgląd zmian ({previews.length} {previews.length === 1 ? 'plik' : previews.length > 1 && previews.length < 5 ? 'pliki' : 'plików'}):
          </p>
          <ul className="text-xs font-mono mt-1 space-y-2">
            {previews.map((previewItem, index) => (
              <li key={index} className="grid grid-cols-[1fr,auto,1fr] gap-2 items-center">
                <span className="truncate text-slate-500 dark:text-slate-400 text-right" title={previewItem.originalName}>
                  {previewItem.originalName}
                </span>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-slate-400 dark:text-slate-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clipRule="evenodd" />
                </svg>
                <span className={`flex items-center truncate ${previewItem.isTooLong ? 'text-amber-600 dark:text-amber-500' : 'text-indigo-600 dark:text-indigo-400'}`} title={previewItem.newName}>
                  {previewItem.isTooLong && (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                      <title>Wygenerowana ścieżka jest bardzo długa (>255 znaków) i może powodować problemy w niektórych systemach plików.</title>
                      <path fillRule="evenodd" d="M8.257 3.099c.636-1.21 2.852-1.21 3.488 0l6.233 11.896c.64 1.223-.453 2.755-1.744 2.755H3.768c-1.291 0-2.384-1.532-1.744-2.755L8.257 3.099zM10 13a1 1 0 110-2 1 1 0 010 2zm-1-4a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" />
                    </svg>
                  )}
                  <span className="truncate">{previewItem.newName}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex justify-end space-x-4 mt-6 pt-4 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 rounded-md hover:bg-slate-200 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-slate-900 focus:ring-slate-500 transition-colors"
          >
            Anuluj
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-slate-900 focus:ring-indigo-500 transition-colors"
          >
            Potwierdź i kontynuuj
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