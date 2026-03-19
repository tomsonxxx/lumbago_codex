
import React from 'react';

interface FeatureItemProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

const FeatureItem: React.FC<FeatureItemProps> = ({ icon, title, description }) => (
  <div className="flex items-start p-4 bg-white/5 dark:bg-slate-800/50 rounded-lg">
    <div className="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-lg bg-indigo-500 text-white">
      {icon}
    </div>
    <div className="ml-4">
      <dt className="text-md font-bold text-slate-900 dark:text-white">{title}</dt>
      <dd className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</dd>
    </div>
  </div>
);

const Roadmap: React.FC = () => {
  const features: FeatureItemProps[] = [
    {
      icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>,
      title: "Konwersja Bibliotek",
      description: "Narzędzia do płynnej konwersji bibliotek między formatami, np. Rekordbox ↔ VirtualDJ, z zachowaniem cue pointów i pętli."
    },
    {
      icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>,
      title: "Analiza Setów DJ-skich",
      description: "Inteligentna analiza playlist i setów pod kątem spójności gatunkowej, progresji energii i kompatybilności harmonicznej."
    },
    {
      icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" /></svg>,
      title: "Zaawansowane Duplikaty",
      description: "Wykrywanie duplikatów na podstawie analizy akustycznej (audio fingerprinting), a nie tylko metadanych."
    },
    {
      icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7.014A8.003 8.003 0 0112 3c1.398 0 2.743.57 3.714 1.486A8.007 8.007 0 0118 9c-2 0-3-2-3-4s.657 1.343 2.657 2.657z" /></svg>,
      title: "Sugestie AI",
      description: "Generowanie propozycji playlist i rekomendacji utworów na podstawie analizy Twojej biblioteki muzycznej."
    },
    {
      icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" /></svg>,
      title: "Synchronizacja z Chmurą",
      description: "Możliwość synchronizacji Twojej biblioteki i jej metadanych z usługami chmurowymi jak Dropbox czy Google Drive."
    },
    {
        icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 6l12-3" /></svg>,
        title: "Wsparcie dla Więcej Tagów",
        description: "Obsługa dodatkowych, zaawansowanych tagów, takich jak klucz harmoniczny (np. Camelot), BPM, energia i inne."
    }
  ];

  return (
    <div className="w-full max-w-4xl mx-auto mt-12 py-8">
      <div className="text-center">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          Plany Rozwoju
        </h2>
        <p className="mt-3 max-w-2xl mx-auto text-md text-slate-500 dark:text-slate-400">
          Lumbago Music AI to projekt w ciągłej ewolucji. Oto funkcje, nad którymi pracujemy, aby stał się on niezastąpionym narzędziem dla każdego DJ-a.
        </p>
      </div>
      <dl className="mt-10 space-y-6 md:space-y-0 md:grid md:grid-cols-2 md:gap-x-8 md:gap-y-6">
        {features.map((feature) => (
          <FeatureItem key={feature.title} {...feature} />
        ))}
      </dl>
    </div>
  );
};

export default Roadmap;