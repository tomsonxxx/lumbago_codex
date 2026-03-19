import React from 'react';

interface PostDownloadModalProps {
  isOpen: boolean;
  onRemove: () => void;
  onKeep: () => void;
  count: number;
}

const getPluralForm = (count: number): string => {
  if (count === 1) return 'plik';
  const lastDigit = count % 10;
  const lastTwoDigits = count % 100;
  if (lastDigit >= 2 && lastDigit <= 4 && (lastTwoDigits < 12 || lastTwoDigits > 14)) {
    return 'pliki';
  }
  return 'plików';
};

const PostDownloadModal: React.FC<PostDownloadModalProps> = ({ isOpen, onRemove, onKeep, count }) => {
  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50 transition-opacity duration-300"
      aria-modal="true"
      role="dialog"
    >
      <div 
        className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-md mx-4 transform transition-all duration-300 scale-95 opacity-0 animate-fade-in-scale"
      >
        <div className="flex items-start">
            <div className="flex-shrink-0 mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 dark:bg-green-900 sm:mx-0 sm:h-10 sm:w-10">
                <svg className="h-6 w-6 text-green-600 dark:text-green-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
            </div>
            <div className="ml-4 text-left">
                 <h2 className="text-xl font-bold text-slate-900 dark:text-white" id="modal-title">Pobieranie zakończone</h2>
                 <div className="mt-2">
                    <p className="text-sm text-slate-600 dark:text-slate-300">
                        Pomyślnie pobrano {count} {getPluralForm(count)}. Co chcesz zrobić z przetworzonymi plikami w kolejce?
                    </p>
                    <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                        Ta operacja nie wpłynie na oryginalne pliki na Twoim dysku.
                    </p>
                </div>
            </div>
        </div>

        <div className="mt-6 flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-4 space-y-2 space-y-reverse sm:space-y-0">
          <button
            onClick={onKeep}
            type="button"
            className="w-full sm:w-auto px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 rounded-md hover:bg-slate-200 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-slate-900 focus:ring-slate-500 transition-colors"
          >
            Zachowaj w kolejce
          </button>
          <button
            onClick={onRemove}
            type="button"
            className="w-full sm:w-auto px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-slate-900 focus:ring-indigo-500 transition-colors"
          >
            Usuń z kolejki
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

export default PostDownloadModal;