import React from 'react';

interface HeaderToolbarProps {
  collectionName?: string;
  totalCount: number;
  selectedCount: number;
  isAnalyzing: boolean;
  isSaving: boolean;
  onAnalyzeAll: () => void;
  onRename: () => void;
  onFindDuplicates: () => void;
  onXmlConvert: () => void;
  isDirectAccessMode: boolean;
  directoryName?: string;
}

const ActionButton: React.FC<{
  onClick: () => void;
  disabled: boolean;
  isLoading?: boolean;
  loadingText?: string;
  title: string;
  children: React.ReactNode;
  variant?: 'default' | 'primary';
}> = ({ onClick, disabled, isLoading = false, loadingText = "Przetwarzam...", title, children, variant = 'default' }) => {
  const baseClasses = "px-4 py-2 text-sm font-bold rounded-lg flex items-center justify-center transition-transform focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-bg-main-start";
  
  const variantClasses = {
    default: "text-text-dim bg-bg-panel-solid hover:bg-slate-700/80 disabled:bg-slate-800/50 focus:ring-accent-cyan",
    primary: "btn-gradient disabled:transform-none disabled:shadow-none focus:ring-accent-green",
  };

  const disabledClasses = "disabled:cursor-not-allowed";
  
  return (
    <button
      onClick={onClick}
      disabled={disabled || isLoading}
      title={title}
      className={`${baseClasses} ${variantClasses[variant]} ${disabledClasses}`}
    >
      {isLoading ? (
          <>
            <span className="btn-spinner !mr-2 h-4 w-4"></span>
            <span>{loadingText}</span>
          </>
      ) : (
        children
      )}
    </button>
  );
};

const HeaderToolbar: React.FC<HeaderToolbarProps> = ({
  collectionName,
  totalCount,
  selectedCount,
  isAnalyzing,
  isSaving,
  onAnalyzeAll,
  onRename,
  onFindDuplicates,
  onXmlConvert,
  isDirectAccessMode,
  directoryName,
}) => {
  const isAnyLoading = isAnalyzing || isSaving;
  const title = collectionName ? `${collectionName}` : 'Wszystkie utwory';

  return (
    <header className="lg:col-span-full p-4 bg-bg-header backdrop-blur-sm rounded-2xl border border-border-color">
        <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
                 <h1 className="text-3xl font-bold flex items-center gap-4">
                    <div>
                        <span className="lumbago">Lumbago</span><span className="music-ai">Music AI</span>
                    </div>
                    <div className="equalizer">
                        <div className="bar"></div><div className="bar"></div><div className="bar"></div><div className="bar"></div><div className="bar"></div>
                    </div>
                </h1>
                <div className="border-l border-border-color h-8"></div>
                 <div className="flex flex-col">
                    <h2 className="text-lg font-semibold text-text-light truncate" title={title}>{title} ({totalCount})</h2>
                    {isDirectAccessMode && (
                        <div className="flex items-center text-xs text-text-dark" title={`Pracujesz w folderze: ${directoryName}`}>
                            <svg xmlns="http://www.w.org/2000/svg" className="h-3 w-3 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm2 2v1h12V8H4z" clipRule="evenodd" /></svg>
                            <span className="truncate max-w-[200px]">{directoryName}</span>
                        </div>
                    )}
                </div>
            </div>
            <div className="flex items-center flex-wrap gap-2">
                 <ActionButton
                    onClick={() => { document.getElementById('file-input')?.click(); }}
                    disabled={isAnyLoading}
                    title="Importuj pliki lub foldery"
                    variant="default"
                >
                    Import
                </ActionButton>
                 <ActionButton
                    onClick={() => alert("Funkcja w przygotowaniu!")}
                    disabled={isAnyLoading}
                    title="Skanuj folder w poszukiwaniu zmian"
                >
                    Scan
                </ActionButton>
                <ActionButton
                    onClick={onAnalyzeAll}
                    disabled={totalCount === 0 || isAnyLoading}
                    isLoading={isAnalyzing}
                    loadingText="Analizuję..."
                    title={"Analizuj wszystkie nieprzetworzone pliki"}
                    variant="primary"
                >
                    Tag AI
                </ActionButton>
                 <ActionButton
                    onClick={onXmlConvert}
                    disabled={isAnyLoading}
                    title="Konwertuj bazę danych Rekordbox/VirtualDJ"
                >
                    Convert XML
                </ActionButton>
                <ActionButton
                    onClick={onFindDuplicates}
                    disabled={totalCount < 2 || isAnyLoading}
                    title="Znajdź duplikaty w bieżącej kolejce"
                >
                    Find Duplicates
                </ActionButton>
                <ActionButton
                    onClick={onRename}
                    disabled={isAnyLoading}
                    title="Ustaw szablon zmiany nazw dla wszystkich plików"
                >
                    Rename
                </ActionButton>
            </div>
        </div>
    </header>
  );
};

export default HeaderToolbar;