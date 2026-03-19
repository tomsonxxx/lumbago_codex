import React from 'react';
import DirectoryConnect from './DirectoryConnect'; // Nowy komponent

interface WelcomeScreenProps {
    children: React.ReactNode; // To będzie FileDropzone
    onDirectoryConnect: (handle: any) => void;
}

const Feature: React.FC<{ icon: React.ReactNode; title: string; description: string }> = ({ icon, title, description }) => (
    <div className="flex flex-col items-center text-center">
        <div className="flex items-center justify-center w-12 h-12 mb-3 rounded-full bg-indigo-100 dark:bg-slate-800 text-indigo-500 dark:text-indigo-400">
            {icon}
        </div>
        <h3 className="text-md font-semibold text-slate-800 dark:text-slate-200">{title}</h3>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>
    </div>
);


const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ children, onDirectoryConnect }) => {
    const isFileSystemAccessSupported = 'showDirectoryPicker' in window;
    
    return (
        <div className="mt-8 text-center animate-fade-in">
             <div className="max-w-3xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-8 mb-10">
                <Feature 
                    icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z" /></svg>}
                    title="Automatyczne Tagowanie"
                    description="AI analizuje nazwy plików, by znaleźć wykonawcę, album, rok i gatunek."
                />
                <Feature 
                    icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
                    title="Pobieranie Okładek"
                    description="Wyszukuje i dołącza okładki albumów w wysokiej rozdzielczości."
                />
                <Feature 
                    icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" /></svg>}
                    title="Inteligentna Zmiana Nazw"
                    description="Automatycznie porządkuje pliki w foldery i zmienia ich nazwy wg schematu."
                />
            </div>
            
            {children}
            
            {isFileSystemAccessSupported && (
                 <>
                    <div className="relative flex items-center w-full max-w-lg mx-auto my-6">
                        <div className="flex-grow border-t border-slate-300 dark:border-slate-700"></div>
                        <span className="flex-shrink mx-4 text-slate-400 dark:text-slate-500 text-sm font-bold">LUB</span>
                        <div className="flex-grow border-t border-slate-300 dark:border-slate-700"></div>
                    </div>
                    <DirectoryConnect onDirectoryConnect={onDirectoryConnect} />
                </>
            )}

        </div>
    );
};

export default WelcomeScreen;