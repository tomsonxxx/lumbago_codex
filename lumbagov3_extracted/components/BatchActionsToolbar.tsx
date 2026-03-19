import React from 'react';
import ActionsDropdown from './ActionsDropdown';

interface BatchActionsToolbarProps {
  selectedCount: number;
  isBatchProcessing: boolean;
  onClearSelection: () => void;
  onProcess: () => void;
  onDownload: () => void;
  onBatchEdit: () => void;
  onDelete: () => void;
  onBatchAnalyze: () => void;
}

const BatchActionsToolbar: React.FC<BatchActionsToolbarProps> = ({
  selectedCount,
  isBatchProcessing,
  onClearSelection,
  onProcess,
  onDownload,
  onBatchEdit,
  onDelete,
  onBatchAnalyze,
}) => {
  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 w-full max-w-2xl z-50 animate-slide-up">
      <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-lg rounded-xl shadow-2xl p-3 flex items-center justify-between mx-4 border border-slate-200 dark:border-slate-700">
        <div className="flex items-center">
            <span className="text-sm font-bold bg-indigo-500 text-white rounded-full h-8 w-8 flex items-center justify-center mr-3">{selectedCount}</span>
            <span className="text-slate-700 dark:text-slate-300 font-medium">zaznaczono</span>
            <button onClick={onClearSelection} className="ml-4 text-xs text-indigo-600 dark:text-indigo-400 hover:underline" disabled={isBatchProcessing}>Wyczyść</button>
        </div>
        <div className="flex items-center space-x-2">
            <button 
                onClick={onBatchAnalyze} 
                disabled={isBatchProcessing}
                className="px-3 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-md hover:bg-indigo-500 disabled:bg-indigo-400 disabled:cursor-wait flex items-center"
            >
                {isBatchProcessing ? (
                    <span className="btn-spinner"></span>
                ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                )}
                <span>{isBatchProcessing ? 'Analizuję...' : 'Analizuj'}</span>
            </button>
            <button 
                onClick={onDownload}
                disabled={isBatchProcessing}
                className="p-2 rounded-md bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 transition-colors disabled:opacity-50"
                title="Pobierz"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
            </button>
            <ActionsDropdown 
                onProcess={onProcess}
                onBatchEdit={onBatchEdit}
                onDelete={onDelete}
                onBatchAnalyze={onBatchAnalyze}
                isDisabled={isBatchProcessing}
            />
        </div>
      </div>
    </div>
  );
};

export default BatchActionsToolbar;