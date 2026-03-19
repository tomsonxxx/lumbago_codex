import React from 'react';

const APP_VERSION = '1.5.0';

const Footer: React.FC = () => {
  return (
    <footer className="w-full max-w-4xl mx-auto text-center py-6 mt-8 border-t border-slate-200 dark:border-slate-800">
      <p className="text-sm text-slate-500 dark:text-slate-500">
        Inteligentny Tagger ID3 - Wersja {APP_VERSION}
      </p>
      <p className="text-xs text-slate-600 dark:text-slate-600 mt-1">
        Stworzone z Gemini AI
      </p>
    </footer>
  );
};

export default Footer;