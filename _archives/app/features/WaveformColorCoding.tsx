
import React, { useState, useRef, useEffect } from 'react';
import { Icons } from '../Icons';

export const WaveformColorCoding = () => {
    const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [fileName, setFileName] = useState<string | null>(null);
    const [vizMode, setVizMode] = useState<'rgb' | 'spectrum'>('rgb');
    
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const animationRef = useRef<number>(0);

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setFileName(file.name);
        const url = URL.createObjectURL(file);
        
        if (audioRef.current) {
            audioRef.current.src = url;
            audioRef.current.load();
        }

        if (!audioContext) {
            const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
            setAudioContext(ctx);
        }
    };

    const togglePlay = async () => {
        if (!audioRef.current || !audioContext) return;

        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }

        if (isPlaying) {
            audioRef.current.pause();
            setIsPlaying(false);
            cancelAnimationFrame(animationRef.current);
        } else {
            // Setup Audio Graph if not exists
            if (!sourceRef.current) {
                const source = audioContext.createMediaElementSource(audioRef.current);
                const analyser = audioContext.createAnalyser();
                analyser.fftSize = 2048; // High resolution
                
                source.connect(analyser);
                analyser.connect(audioContext.destination);
                
                sourceRef.current = source;
                analyserRef.current = analyser;
            }

            audioRef.current.play();
            setIsPlaying(true);
            renderFrame();
        }
    };

    const renderFrame = () => {
        if (!analyserRef.current || !canvasRef.current) return;
        
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserRef.current.getByteFrequencyData(dataArray);

        const width = canvas.width;
        const height = canvas.height;
        ctx.clearRect(0, 0, width, height);

        if (vizMode === 'spectrum') {
            const barWidth = (width / bufferLength) * 2.5;
            let barHeight;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                barHeight = dataArray[i] / 255 * height;
                
                // Color based on frequency
                // Lows (Red), Mids (Green), Highs (Blue)
                const r = i < bufferLength / 3 ? 255 : 0;
                const g = i >= bufferLength / 3 && i < 2 * bufferLength / 3 ? 255 : 0;
                const b = i >= 2 * bufferLength / 3 ? 255 : 0;

                ctx.fillStyle = `rgb(${r},${g},${b})`;
                ctx.fillRect(x, height - barHeight, barWidth, barHeight);
                x += barWidth + 1;
            }
        } else {
            // RGB Waveform Simulation
            // We'll calculate energy in 3 bands to determine color intensity for the wave
            
            // Split array into 3 bands
            const split = Math.floor(bufferLength / 3);
            const lows = dataArray.slice(0, split).reduce((a,b)=>a+b) / split;
            const mids = dataArray.slice(split, split*2).reduce((a,b)=>a+b) / split;
            const highs = dataArray.slice(split*2).reduce((a,b)=>a+b) / split;

            // Normalize 0-1
            const r = Math.min(255, lows * 1.5); // Boost bass visibility
            const g = Math.min(255, mids * 1.2);
            const b = Math.min(255, highs * 1.5);

            // Draw a time-domain-like representation modulated by frequency energy
            // Since getByteFrequencyData is FFT, we simulate a "colored" osciloscope
            // In a real advanced app, we'd process the time domain buffer directly.
            
            ctx.lineWidth = 2;
            ctx.strokeStyle = `rgb(${r}, ${g}, ${b})`;
            ctx.beginPath();
            
            const sliceWidth = width * 1.0 / bufferLength;
            let x = 0;

            for(let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * height / 2;

                if(i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);

                x += sliceWidth;
            }
            ctx.stroke();

            // Add Labels
            ctx.font = "12px monospace";
            ctx.fillStyle = "rgba(255, 100, 100, 0.8)";
            ctx.fillText(`LOW: ${Math.round(lows)}`, 10, 20);
            ctx.fillStyle = "rgba(100, 255, 100, 0.8)";
            ctx.fillText(`MID: ${Math.round(mids)}`, 10, 35);
            ctx.fillStyle = "rgba(100, 100, 255, 0.8)";
            ctx.fillText(`HI:  ${Math.round(highs)}`, 10, 50);
        }

        animationRef.current = requestAnimationFrame(renderFrame);
    };

    return (
        <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h3 className="text-xl font-bold text-gray-200 flex items-center gap-2">
                            <Icons.Palette /> RGB Waveform Analyzer
                        </h3>
                        <p className="text-sm text-gray-400 mt-1">
                            Visualize track structure by frequency color (Red=Bass, Green=Mids, Blue=Highs).
                        </p>
                    </div>
                    <div className="flex bg-gray-700 rounded p-1">
                        <button 
                            onClick={() => setVizMode('rgb')}
                            className={`px-3 py-1 rounded text-xs font-bold transition-colors ${vizMode === 'rgb' ? 'bg-gray-600 text-white shadow' : 'text-gray-400 hover:text-gray-200'}`}
                        >
                            RGB Wave
                        </button>
                        <button 
                            onClick={() => setVizMode('spectrum')}
                            className={`px-3 py-1 rounded text-xs font-bold transition-colors ${vizMode === 'spectrum' ? 'bg-gray-600 text-white shadow' : 'text-gray-400 hover:text-gray-200'}`}
                        >
                            Spectrum
                        </button>
                    </div>
                </div>

                <div className="mb-6 flex gap-4 items-center">
                    <input 
                        type="file" 
                        accept="audio/*"
                        onChange={handleFileUpload} 
                        className="text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
                    />
                    {fileName && (
                        <button 
                            onClick={togglePlay}
                            className={`px-6 py-2 rounded-full font-bold text-white transition-all shadow-lg flex items-center gap-2 ${isPlaying ? 'bg-yellow-600 hover:bg-yellow-500' : 'bg-green-600 hover:bg-green-500'}`}
                        >
                            {isPlaying ? <><Icons.Pause width={18}/> Pause Analysis</> : <><Icons.Play width={18}/> Start Analysis</>}
                        </button>
                    )}
                </div>

                <div className="relative bg-black rounded-lg border border-gray-600 overflow-hidden shadow-inner">
                    <canvas 
                        ref={canvasRef} 
                        width={1024} 
                        height={300} 
                        className="w-full h-[300px]"
                    />
                    {!fileName && (
                        <div className="absolute inset-0 flex items-center justify-center text-gray-600">
                            Upload a track to visualize frequencies
                        </div>
                    )}
                </div>

                {/* Hidden Audio Element */}
                <audio ref={audioRef} onEnded={() => setIsPlaying(false)} className="hidden" />

                <div className="mt-6 grid grid-cols-3 gap-4 text-center">
                    <div className="p-3 rounded bg-red-900/20 border border-red-900/50">
                        <div className="text-red-500 font-bold mb-1">LOW (Bass)</div>
                        <div className="text-xs text-gray-400">0Hz - 250Hz</div>
                        <div className="text-xs text-gray-500 mt-1">Kicks, Basslines</div>
                    </div>
                    <div className="p-3 rounded bg-green-900/20 border border-green-900/50">
                        <div className="text-green-500 font-bold mb-1">MID (Vocals)</div>
                        <div className="text-xs text-gray-400">250Hz - 4kHz</div>
                        <div className="text-xs text-gray-500 mt-1">Vocals, Synths, Guitars</div>
                    </div>
                    <div className="p-3 rounded bg-blue-900/20 border border-blue-900/50">
                        <div className="text-blue-500 font-bold mb-1">HIGH (Perc)</div>
                        <div className="text-xs text-gray-400">4kHz - 20kHz</div>
                        <div className="text-xs text-gray-500 mt-1">Hi-Hats, Cymbals, Air</div>
                    </div>
                </div>
            </div>
        </div>
    );
};
