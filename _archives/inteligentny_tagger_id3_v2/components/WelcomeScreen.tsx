import React from 'react';
import DirectoryConnect from './DirectoryConnect';

interface WelcomeScreenProps {
    children: React.ReactNode; // To będzie FileDropzone
    onDirectoryConnect: (handle: any) => void;
}

const QuickStartStep: React.FC<{ num: number; title: string; description: string; delay: string }> = ({ num, title, description, delay }) => (
    <div className={`quick-start-step animate-fade-in-up ${delay}`}>
        <div className="step-number">{num}</div>
        <h3 className="text-lg font-semibold text-accent-cyan mb-2">{title}</h3>
        <p className="text-sm text-text-dim">{description}</p>
    </div>
);

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ children, onDirectoryConnect }) => {
    const isFileSystemAccessSupported = 'showDirectoryPicker' in window;
    
    return (
        <div className="container mx-auto px-4 py-8 mt-8 text-center animate-fade-in">
            <h1 className="text-6xl font-bold mb-4">
                <span className="lumbago">Lumbago</span> <span className="music-ai">Music AI</span>
            </h1>
            <p className="text-xl text-text-dim mb-12">
                Twoja biblioteka muzyczna. Zawsze perfekcyjna.
            </p>

            <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
                <QuickStartStep
                    num={1}
                    title="Dodaj Muzykę"
                    description="Przeciągnij pliki lub połącz się z całym folderem, aby rozpocząć."
                    delay="delay-1"
                />
                <QuickStartStep
                    num={2}
                    title="Analiza AI"
                    description="Kliknij 'Tag AI', aby automatycznie uzupełnić tagi, okładki i tonacje."
                    delay="delay-2"
                />
                <QuickStartStep
                    num={3}
                    title="Zapisz Zmiany"
                    description="Pobierz otagowane pliki jako ZIP lub zapisz zmiany bezpośrednio na dysku."
                    delay="delay-3"
                />
            </div>

            {children}
            
            {isFileSystemAccessSupported && (
                 <>
                    <div className="relative flex items-center w-full max-w-lg mx-auto my-6">
                        <div className="flex-grow border-t border-border-color"></div>
                        <span className="flex-shrink mx-4 text-text-dark text-sm font-bold">LUB</span>
                        <div className="flex-grow border-t border-border-color"></div>
                    </div>
                    <DirectoryConnect onDirectoryConnect={onDirectoryConnect} />
                </>
            )}
        </div>
    );
};

export default WelcomeScreen;