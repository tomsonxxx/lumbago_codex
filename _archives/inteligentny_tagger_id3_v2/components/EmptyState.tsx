import React from 'react';

interface EmptyStateProps {
    viewType: 'all' | 'collection' | 'playlist';
}

const EmptyState: React.FC<EmptyStateProps> = ({ viewType }) => {

    const messages = {
        all: {
            icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" /></svg>,
            title: "Twoja biblioteka jest pusta",
            description: "Kliknij przycisk 'Połącz z Folderem' lub przeciągnij pliki, aby rozpocząć."
        },
        collection: {
            icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>,
            title: "Brak pasujących utworów",
            description: "Żaden z utworów w Twojej bibliotece nie spełnia kryteriów tej inteligentnej kolekcji."
        },
        playlist: {
             icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" /></svg>,
            title: "Playlista jest pusta",
            description: "Przeciągnij utwory z głównej biblioteki na nazwę tej playlisty, aby je dodać."
        }
    };

    const currentMessage = messages[viewType] || messages.all;

    return (
        <div className="flex flex-col items-center justify-center h-full text-center p-8">
            {currentMessage.icon}
            <h3 className="mt-4 text-lg font-semibold text-slate-300">{currentMessage.title}</h3>
            <p className="mt-1 text-sm text-slate-500">{currentMessage.description}</p>
        </div>
    );
};

export default EmptyState;