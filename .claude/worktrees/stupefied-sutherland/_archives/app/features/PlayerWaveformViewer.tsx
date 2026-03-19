
import React, { useState, useRef, useEffect } from 'react';
import { Icons } from '../Icons';

export const PlayerWaveformViewer = () => {
    const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
    const [audioBuffer, setAudioBuffer] = useState<AudioBuffer | null>(null);
    const [sourceNode, setSourceNode] = useState<AudioBufferSourceNode | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [fileName, setFileName] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [volume, setVolume] = useState(1);
    const [zoomLevel, setZoomLevel] = useState(1);

    const canvasRef = useRef<HTMLCanvasElement>(null);
    const requestRef = useRef<number>(0);
    const startTimeRef = useRef<number>(0);
    const pauseTimeRef = useRef<number>(0);

    const gainNodeRef = useRef<GainNode | null>(null);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (sourceNode) sourceNode.stop();
        setIsPlaying(false);
        setCurrentTime(0);
        pauseTimeRef.current = 0;
        setFileName(file.name);
        setError(null);

        let ctx = audioContext;
        if (!ctx) {
            const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
            ctx = new AudioContextClass();
            setAudioContext(ctx);
        }

        try {
            const arrayBuffer = await file.arrayBuffer();
            if (!ctx) return;
            const decodedBuffer = await ctx.decodeAudioData(arrayBuffer);
            setAudioBuffer(decodedBuffer);
            setDuration(decodedBuffer.duration);
            drawWaveform(decodedBuffer, 1);
        } catch (err) {
            console.error("Error decoding:", err);
            setError("Failed to decode audio file.");
        }
    };

    const playAudio = () => {
        if (!audioContext || !audioBuffer) return;

        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }

        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        
        const gainNode = audioContext.createGain();
        gainNode.gain.value = volume;
        gainNodeRef.current = gainNode;

        source.connect(gainNode);
        gainNode.connect(audioContext.destination);

        const startOffset = pauseTimeRef.current;
        source.start(0, startOffset);
        
        startTimeRef.current = audioContext.currentTime - startOffset;
        setSourceNode(source);
        setIsPlaying(true);

        source.onended = () => {
            setIsPlaying(false);
            if (audioContext.currentTime - startTimeRef.current >= audioBuffer.duration) {
                pauseTimeRef.current = 0;
                setCurrentTime(0);
            }
        };
    };

    const pauseAudio = () => {
        if (sourceNode && audioContext) {
            sourceNode.stop();
            pauseTimeRef.current = audioContext.currentTime - startTimeRef.current;
            setIsPlaying(false);
            setSourceNode(null);
        }
    };

    const stopAudio = () => {
        if (sourceNode) {
            sourceNode.stop();
        }
        setIsPlaying(false);
        setSourceNode(null);
        pauseTimeRef.current = 0;
        setCurrentTime(0);
    };

    const handleSeek = (e: React.MouseEvent<HTMLCanvasElement>) => {
        if (!audioBuffer || !canvasRef.current) return;
        const rect = canvasRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const width = rect.width;
        
        const clickRatio = x / width;
        const newTime = clickRatio * duration;

        pauseTimeRef.current = newTime;
        setCurrentTime(newTime);
        
        if (isPlaying) {
            if (sourceNode) sourceNode.stop();
            playAudio();
        }
    };

    useEffect(() => {
        const animate = () => {
            if (isPlaying && audioContext) {
                const now = audioContext.currentTime - startTimeRef.current;
                setCurrentTime(now);
                requestRef.current = requestAnimationFrame(animate);
            }
        };
        if (isPlaying) {
            requestRef.current = requestAnimationFrame(animate);
        }
        return () => cancelAnimationFrame(requestRef.current);
    }, [isPlaying, audioContext]);

    useEffect(() => {
        if (gainNodeRef.current) {
            gainNodeRef.current.gain.value = volume;
        }
    }, [volume]);

    useEffect(() => {
        if (audioBuffer) {
            drawWaveform(audioBuffer, zoomLevel);
        }
    }, [audioBuffer, zoomLevel]);

    const drawWaveform = (buffer: AudioBuffer, zoom: number) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const width = canvas.width;
        const height = canvas.height;
        ctx.clearRect(0, 0, width, height);

        const data = buffer.getChannelData(0);
        const step = Math.ceil(data.length / width / zoom);
        const amp = height / 2;

        ctx.fillStyle = '#4fd1c5';
        ctx.beginPath();
        
        for (let i = 0; i < width; i++) {
            let min = 1.0;
            let max = -1.0;
            
            for (let j = 0; j < step; j++) {
                const datum = data[(i * step) + j];
                if (datum < min) min = datum;
                if (datum > max) max = datum;
            }
            
            ctx.fillRect(i, (1 + min) * amp, 1, Math.max(1, (max - min) * amp));
        }
    };

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !audioBuffer) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        
        drawWaveform(audioBuffer, zoomLevel);

        const x = (currentTime / duration) * canvas.width;
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(x, 0, 2, canvas.height);

    }, [currentTime, audioBuffer, zoomLevel, duration]);

    const formatTime = (t: number) => {
        const m = Math.floor(t / 60);
        const s = Math.floor(t % 60);
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4 bg-gray-800 p-4 rounded-lg border border-gray-700">
                <input 
                    type="file" 
                    accept="audio/*"
                    onChange={handleFileUpload} 
                    className="text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"
                />
                <div className="text-gray-300 truncate font-medium">{fileName || "No file selected"}</div>
            </div>

            {error && <div className="text-red-400 text-sm">{error}</div>}

            <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 flex flex-col items-center gap-6">
                <div className="w-full relative group">
                    <canvas 
                        ref={canvasRef} 
                        width={800} 
                        height={128} 
                        className="w-full h-32 bg-gray-950 rounded cursor-pointer"
                        onClick={handleSeek}
                    />
                </div>

                <div className="w-full flex justify-between text-xs text-gray-500 font-mono">
                    <span>{formatTime(currentTime)}</span>
                    <span>{formatTime(duration)}</span>
                </div>

                <div className="flex items-center gap-8">
                     <button onClick={stopAudio} className="p-3 bg-gray-700 rounded-full hover:bg-gray-600">
                         <Icons.Square /> 
                     </button>
                     <button onClick={isPlaying ? pauseAudio : playAudio} className="p-4 bg-blue-500 rounded-full hover:bg-blue-400 text-white shadow-lg shadow-blue-500/20">
                         {isPlaying ? <Icons.Pause /> : <Icons.Play />}
                     </button>
                </div>
                
                <div className="w-full flex items-center gap-4">
                     <span className="text-xs text-gray-500">Vol</span>
                     <input 
                        type="range" min="0" max="1" step="0.01" 
                        value={volume} onChange={e => setVolume(parseFloat(e.target.value))}
                        className="w-32 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                     />
                     <span className="text-xs text-gray-500 ml-4">Zoom</span>
                     <input 
                        type="range" min="0.5" max="5" step="0.1" 
                        value={zoomLevel} onChange={e => setZoomLevel(parseFloat(e.target.value))}
                        className="w-32 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                     />
                </div>
            </div>
        </div>
    );
};
