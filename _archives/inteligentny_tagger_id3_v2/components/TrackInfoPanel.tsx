import React, { useEffect, useRef, useState, useCallback } from 'react';
import { AudioFile, ID3Tags, Hotcue } from '../types';
import AlbumCover from './AlbumCover';
import { formatTime } from '../utils/formatUtils';

// Assume WaveSurfer is loaded globally
declare const WaveSurfer: any;
// Assume Spectrogram plugin is loaded globally
declare const Spectrogram: any;

interface TrackInfoPanelProps {
    selectedFile: AudioFile | null;
    onSetHotcue: (fileId: string, hotcue: Hotcue) => void;
    onNext: () => void;
    onPrev: () => void;
}

const TrackInfoPanel: React.FC<TrackInfoPanelProps> = ({ selectedFile, onSetHotcue, onNext, onPrev }) => {
    const waveformRef = useRef<HTMLDivElement>(null);
    const spectrogramRef = useRef<HTMLDivElement>(null);
    const wavesurfer = useRef<any>(null);

    const [isPlaying, setIsPlaying] = useState(false);
    const [isLooping, setIsLooping] = useState(false);
    const [volume, setVolume] = useState(0.75);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [zoomLevel, setZoomLevel] = useState(1);
    const [showSpectrogram, setShowSpectrogram] = useState(false);
    const [pitch, setPitch] = useState(1.0);
    
    const selectedFileTags = selectedFile?.fetchedTags || selectedFile?.originalTags;

    const setupWaveSurfer = useCallback(() => {
        if (waveformRef.current && spectrogramRef.current) {
            destroyWaveSurfer(); // Destroy existing instance before creating a new one
            
            wavesurfer.current = WaveSurfer.create({
                container: waveformRef.current,
                waveColor: 'rgba(142, 240, 255, 0.5)',
                progressColor: 'rgb(255, 102, 204)',
                barWidth: 3,
                barRadius: 3,
                barGap: 2,
                height: 100,
                cursorWidth: 2,
                cursorColor: '#39ff14',
                responsive: true,
                hideScrollbar: true,
                minPxPerSec: zoomLevel,
                plugins: [
                    Spectrogram.create({
                        container: spectrogramRef.current,
                        labels: false,
                        height: 100,
                        colorMap: 'viridis',
                    }),
                ],
            });

            wavesurfer.current.on('play', () => setIsPlaying(true));
            wavesurfer.current.on('pause', () => setIsPlaying(false));
            wavesurfer.current.on('finish', () => {
                setIsPlaying(false);
                if (isLooping) {
                    wavesurfer.current.play();
                }
            });
            wavesurfer.current.on('timeupdate', (time: number) => setCurrentTime(time));
            wavesurfer.current.on('ready', (newDuration: number) => {
                setDuration(newDuration);
                setCurrentTime(0);
                setZoomLevel(1);
                setPitch(1.0);
                wavesurfer.current.setPlaybackRate(1.0);

                const canvas = wavesurfer.current.getWrapper().querySelector('wave > canvas');
                if (canvas) {
                    const ctx = canvas.getContext('2d');
                    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height * 1.5);
                    gradient.addColorStop(0, '#ff66cc'); // magenta
                    gradient.addColorStop(1, '#8ef0ff'); // cyan
                    wavesurfer.current.setOptions({ progressColor: gradient });
                }
            });
        }
    }, [isLooping, zoomLevel]); // Add zoomLevel to dependencies

    const destroyWaveSurfer = useCallback(() => {
        if (wavesurfer.current) {
            wavesurfer.current.destroy();
            wavesurfer.current = null;
        }
    }, []);

    useEffect(() => {
        setupWaveSurfer();
        return () => destroyWaveSurfer();
    }, [setupWaveSurfer, destroyWaveSurfer]);

    useEffect(() => {
        if (selectedFile && wavesurfer.current) {
            const url = URL.createObjectURL(selectedFile.file);
            wavesurfer.current.load(url);
            wavesurfer.current.on('decode', () => URL.revokeObjectURL(url));
        } else if (!selectedFile && wavesurfer.current) {
            wavesurfer.current.empty();
        }
    }, [selectedFile]);
    
    useEffect(() => { if (wavesurfer.current) wavesurfer.current.setVolume(volume); }, [volume]);
    useEffect(() => { if (wavesurfer.current) wavesurfer.current.zoom(zoomLevel); }, [zoomLevel]);
    useEffect(() => { if (wavesurfer.current) wavesurfer.current.setPlaybackRate(pitch, false); }, [pitch]);
    
    const handlePlayPause = () => { if (wavesurfer.current) wavesurfer.current.playPause(); };
    const handleLoopToggle = () => setIsLooping(prevState => !prevState);

    const handleHotcueSet = useCallback((num: number) => {
        if (wavesurfer.current && selectedFile) {
            const time = wavesurfer.current.getCurrentTime();
            onSetHotcue(selectedFile.id, { num, time });
        }
    }, [selectedFile, onSetHotcue]);

    const handleHotcueTrigger = (num: number) => {
        if (selectedFile && duration > 0) {
            const cue = selectedFile.hotcues.find(c => c.num === num);
            if (cue && wavesurfer.current) {
                wavesurfer.current.seekTo(cue.time / duration);
            }
        }
    };
    
     useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (['1', '2', '3', '4'].includes(e.key)) {
                if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') return;
                e.preventDefault();
                const cueNum = parseInt(e.key);
                if (e.ctrlKey || e.metaKey) handleHotcueSet(cueNum);
                else handleHotcueTrigger(cueNum);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleHotcueSet, handleHotcueTrigger]);

    return (
        <aside className="panel hidden lg:flex flex-col">
            <h2 className="text-xl font-bold mb-4" style={{color: 'var(--accent-magenta)'}}>📀 Track Info</h2>
            {selectedFile ? (
            <div className="flex-grow flex flex-col gap-4 min-h-0">
                <AlbumCover tags={selectedFileTags} className="w-full h-auto aspect-square" />
                <div>
                    <h3 className="text-lg font-bold text-text-light truncate" title={selectedFileTags?.title}>{selectedFileTags?.title || 'Brak tytułu'}</h3>
                    <p className="text-md text-text-dim truncate" title={selectedFileTags?.artist}>{selectedFileTags?.artist || 'Brak artysty'}</p>
                    <p className="text-sm text-text-dark truncate" title={selectedFileTags?.album}>{selectedFileTags?.album || 'Brak albumu'}</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="bg-bg-panel-solid p-2 rounded-lg"><strong>BPM:</strong> {selectedFileTags?.bpm ? Math.round(selectedFileTags.bpm) : '-'}</div>
                    <div className="bg-bg-panel-solid p-2 rounded-lg"><strong>Tonacja:</strong> {selectedFileTags?.key || '-'}</div>
                </div>
                 <button className="w-full py-2 font-bold rounded-lg btn-gradient-secondary">
                    Edit Tags
                </button>
                
                <div className="mt-auto flex flex-col gap-3">
                    <div className="waveform-container cursor-pointer">
                        <div ref={waveformRef} style={{ display: showSpectrogram ? 'none' : 'block' }}></div>
                        <div ref={spectrogramRef} className="spectrogram-container" style={{ display: showSpectrogram ? 'block' : 'none' }}></div>
                        <div className="absolute top-0 left-0 w-full h-full">
                            {duration > 0 && selectedFile.hotcues.map(cue => (
                               <div key={cue.num} className="hotcue-marker" data-cue={cue.num} style={{ left: `${(cue.time / duration) * 100}%` }}></div>
                            ))}
                        </div>
                    </div>
                    <div className="flex justify-between items-center text-xs font-mono text-text-dark">
                        <span>{formatTime(currentTime)}</span>
                        <span>{formatTime(duration)}</span>
                    </div>
                    
                     <div className="flex items-center gap-2">
                        <label htmlFor="zoom" className="text-xs text-text-dark whitespace-nowrap">Zoom:</label>
                        <input type="range" id="zoom" min="1" max="200" value={zoomLevel} onChange={(e) => setZoomLevel(Number(e.target.value))} className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer range-sm" />
                    </div>

                    <div className="flex items-center justify-between gap-2 h-14">
                        <div className="flex items-center gap-2">
                            <button onClick={onPrev} title="Poprzedni utwór" className="p-3 bg-bg-panel-solid text-text-dim rounded-full hover:bg-slate-700 transition"><svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M8.447 14.854a1 1 0 01-1.414-1.414L10.586 10 7.033 6.56A1 1 0 018.447 5.146l4 4a1 1 0 010 1.414l-4 4z" transform="scale(-1 1) translate(-20 0)" /></svg></button>
                            <button onClick={handlePlayPause} className="p-4 bg-accent-magenta text-bg-main rounded-full hover:opacity-80 transition">
                                {isPlaying ? 
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg> :
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
                                }
                            </button>
                             <button onClick={onNext} title="Następny utwór" className="p-3 bg-bg-panel-solid text-text-dim rounded-full hover:bg-slate-700 transition"><svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M8.447 14.854a1 1 0 01-1.414-1.414L10.586 10 7.033 6.56A1 1 0 018.447 5.146l4 4a1 1 0 010 1.414l-4 4z"/></svg></button>
                        </div>
                        <div className="flex items-center gap-2">
                             <button onClick={handleLoopToggle} title="Zapętl" className={`p-2 rounded-full transition-colors ${isLooping ? 'bg-accent-magenta text-bg-main' : 'bg-bg-panel-solid text-text-dim hover:bg-slate-700'}`}><svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 110 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" /></svg></button>
                             <button onClick={() => setShowSpectrogram(s => !s)} title="Przełącz widok" className={`p-2 rounded-full transition-colors ${showSpectrogram ? 'bg-accent-cyan text-bg-main' : 'bg-bg-panel-solid text-text-dim hover:bg-slate-700'}`}><svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" /></svg></button>
                        </div>
                        <div className="channel-meters">
                            <div className="meter-bar"><div className={`meter-level meter-level-l ${isPlaying ? 'playing' : ''}`}></div></div>
                            <div className="meter-bar"><div className={`meter-level meter-level-r ${isPlaying ? 'playing' : ''}`}></div></div>
                        </div>
                    </div>
                     <div className="flex items-center gap-2">
                        <label htmlFor="pitch" className="text-xs text-text-dark whitespace-nowrap">Pitch:</label>
                        <input type="range" id="pitch" min="0.5" max="1.5" step="0.01" value={pitch} onChange={(e) => setPitch(Number(e.target.value))} className="pitch-slider w-full" />
                        <span className="text-xs font-mono text-center w-12">{pitch.toFixed(2)}x</span>
                        <button onClick={() => setPitch(1.0)} className="text-xs bg-bg-panel-solid p-1 rounded hover:bg-slate-700">Reset</button>
                    </div>
                     <div className="grid grid-cols-4 gap-2">
                         {[1, 2, 3, 4].map(num => (
                             <button
                                 key={num}
                                 onClick={() => handleHotcueTrigger(num)}
                                 onContextMenu={(e) => { e.preventDefault(); handleHotcueSet(num); }}
                                 className={`p-2 rounded-md text-sm font-bold transition-colors ${selectedFile.hotcues.some(c => c.num === num) ? 'bg-accent-green text-bg-main' : 'bg-bg-panel-solid text-text-dim hover:bg-slate-700'}`}
                                 title={`Kliknij, aby przejść do Cue ${num}. PPM lub Ctrl+Klik, aby ustawić.`}
                             >
                                 CUE {num}
                             </button>
                         ))}
                    </div>
                </div>
            </div>
            ) : (
            <div className="flex-grow flex items-center justify-center text-text-dark">
                <p>Wybierz utwór z listy, aby zobaczyć szczegóły i odtwarzacz.</p>
            </div>
            )}
        </aside>
    );
};

export default TrackInfoPanel;