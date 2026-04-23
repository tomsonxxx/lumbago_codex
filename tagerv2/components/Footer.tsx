import React from "react";

const APP_VERSION = "1.6.0-dev"; // Updated version for new features

const Footer: React.FC = () => {
  return (
    <footer className="w-full max-w-4xl mx-auto text-center py-6 mt-8 border-t border-[var(--border-color)] dark:border-[var(--border-color)]">
      <p className="text-sm text-[var(--text-secondary)] dark:text-[var(--text-secondary)]">
        Lumbago Music AI - Wersja {APP_VERSION}
      </p>
      <p className="text-xs text-[var(--text-secondary)] dark:text-[var(--text-secondary)] mt-1">
        Stworzone z Gemini AI
      </p>
    </footer>
  );
};

export default Footer;
