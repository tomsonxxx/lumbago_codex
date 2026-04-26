import React, { useState, useEffect } from "react";

declare global {
  interface Window {
    showDirectoryPicker?: (options?: any) => Promise<any>;
  }
}

interface DirectoryConnectProps {
  onDirectoryConnect: (handle: any) => void;
}

const DirectoryConnect: React.FC<DirectoryConnectProps> = ({
  onDirectoryConnect,
}) => {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isIframe, setIsIframe] = useState(false);

  useEffect(() => {
    // Detect if running inside an iframe to warn user proactively
    const checkIframe = () => {
      try {
        return window.self !== window.top;
      } catch (e) {
        return true;
      }
    };
    setIsIframe(checkIframe());
  }, []);

  const handleConnect = async () => {
    setErrorMessage(null);

    const aiStudio = (window as any).aistudio;

    // Proactive check: If we are in an iframe and no bridge exists, warn immediately.
    if (isIframe && !aiStudio) {
      setErrorMessage(
        "⚠️ Dostęp do folderów jest zablokowany przez przeglądarkę w trybie podglądu (iframe). " +
          "Aby skorzystać z tej funkcji, otwórz aplikację w nowej karcie.",
      );
      return;
    }

    try {
      // 1. Try AI Studio brokered API (if available)
      if (aiStudio && aiStudio.showDirectoryPicker) {
        const handle = await aiStudio.showDirectoryPicker({
          mode: "readwrite",
        });
        onDirectoryConnect(handle);
        return;
      }

      // 2. Try Standard Browser API
      if (typeof window.showDirectoryPicker === "function") {
        const handle = await window.showDirectoryPicker({ mode: "readwrite" });
        onDirectoryConnect(handle);
        return;
      }

      throw new Error(
        "Twoja przeglądarka nie obsługuje File System Access API.",
      );
    } catch (error: any) {
      // Handle User Cancellation
      if (error.name === "AbortError") {
        return;
      }

      // Handle Security/Iframe Restrictions specifically
      const isSecurityError = error.name === "SecurityError";
      const isCrossOriginError =
        error.message &&
        (error.message.includes("Cross origin") ||
          error.message.includes("sub frames") ||
          error.message.includes("SecurityError"));

      if (isSecurityError || isCrossOriginError) {
        console.warn("Directory Access Blocked:", error);
        setErrorMessage(
          "⚠️ Błąd bezpieczeństwa: Przeglądarka zablokowała dostęp do plików w tej ramce. " +
            "Otwórz stronę w osobnej karcie (Open in New Tab), aby skorzystać z Trybu Folderu.",
        );
      } else {
        console.error("Directory Connect Error:", error);
        setErrorMessage(
          `Nie udało się połączyć: ${error.message || "Nieznany błąd"}`,
        );
      }
    }
  };

  const aiStudio = (window as any).aistudio;

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] rounded-none border-2 border-dashed border-[var(--border-color)] dark:border-[var(--border-color)]">
      <div className="flex items-center text-[var(--accent-primary)] dark:text-[var(--accent-primary)] mb-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-8 w-8 mr-3"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
          <path
            stroke="#fff"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M10 11V7m0 8v-2"
          />
        </svg>
        <h3 className="text-lg font-bold text-[var(--text-secondary)] dark:text-[var(--text-secondary)]">
          Tryb Folderu (Eksperymentalny)
        </h3>
      </div>
      <p className="max-w-md text-xs text-center text-[var(--text-secondary)] dark:text-[var(--text-secondary)] mb-4">
        Edytuj pliki bezpośrednio na dysku bez tworzenia kopii ZIP. Wymaga
        przeglądarki opartej na Chromium (Chrome, Edge, Brave) i otwarcia w
        pełnej karcie.
      </p>

      {errorMessage && (
        <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 text-xs rounded-none border border-amber-200 dark:border-amber-800 max-w-md text-center">
          {errorMessage}
        </div>
      )}

      <button
        onClick={handleConnect}
        className="px-5 py-2 text-sm font-semibold text-white bg-[var(--accent-secondary)] rounded-none hover:bg-[var(--accent-secondary)] shadow-md transition-all active:scale-95 flex items-center"
      >
        {isIframe && !aiStudio && (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4 mr-2 text-[var(--accent-primary)]"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z"
              clipRule="evenodd"
            />
          </svg>
        )}
        Wybierz Folder
      </button>
    </div>
  );
};

export default DirectoryConnect;
