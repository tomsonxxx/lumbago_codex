
import React, { useState, useRef, useEffect } from 'react';
import { Icons } from '../Icons';

export const SetRecorderAnalyzer = () => {
    const [isRecording, setIsRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisReport, setAnalysisReport] = useState<any | null>(null);
    const [volumeLevel, setVolumeLevel] = useState(0);

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const timerRef = useRef<number>(0);
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const animationFrameRef = useRef<number>(0);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Setup Audio Context for Analysis/Visualizer
            const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
            const analyser = audioCtx.createAnalyser();
            const source = audioCtx.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 256;
            
            audioContextRef.current = audioCtx;
            analyserRef.current = analyser;
            sourceRef.current = source;

            // Setup Media Recorder
            const recorder = new MediaRecorder(stream);
            const chunks: BlobPart[] = [];

            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunks.push(e.data);
            };

            recorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'audio/webm' });
                setAudioBlob(blob);
                
                // Cleanup
                stream.getTracks().forEach(track => track.stop());
                if (audioContextRef.current) audioContextRef.current.close();
                cancelAnimationFrame(animationFrameRef.current);
                setVolumeLevel(0);
            };

            recorder.start();
            mediaRecorderRef.current = recorder;
            setIsRecording(true);
            setAnalysisReport(null);
            setRecordingTime(0);

            // Start Timer
            const startTime = Date.now();
            timerRef.current = window.setInterval(() => {
                setRecordingTime(Math.floor((Date.now() - startTime) / 1000));
            }, 1000);

            // Start Visualizer Loop
            const updateVolume = () => {
                if (!analyser) return;
                const dataArray = new Uint8Array(analyser.frequencyBinCount);
                analyser.getByteFrequencyData(dataArray);
                
                // Simple average volume
                const avg = dataArray.reduce((a, b) => a + b) / dataArray.length;
                setVolumeLevel(avg); // 0-255

                animationFrameRef.current = requestAnimationFrame(updateVolume);
            };
            updateVolume();

        } catch (err) {
            console.error("Error accessing microphone:", err);
            alert("Could not access microphone. Please ensure permissions are granted.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            clearInterval(timerRef.current);
        }
    };

    const analyzeRecording = async () => {
        if (!audioBlob) return;
        setIsAnalyzing(true);
        
        // Simulate heavy analysis process
        await new Promise(resolve => setTimeout(resolve, 2500));

        // Mock Report Data
        const report = {
            duration: formatTime(recordingTime),
            transitionScore: Math.floor(Math.random() * (98 - 70) + 70),
            bpmAccuracy: Math.floor(Math.random() * (100 - 85) + 85),
            energyGraph: Array.from({ length: 20 }, () => Math.floor(Math.random() * 100)),
            detectedTracks: [
                { time: '00:00', title: 'Deep Intro', artist: 'Artist A' },
                { time: '03:45', title: 'Tech Groove', artist: 'Artist B' },
                { time: '06:20', title: 'Vocals', artist: 'Artist C' },
                { time: '09:15', title: 'Outro Mix', artist: 'Artist D' },
            ]
        };

        setAnalysisReport(report);
        setIsAnalyzing(false);
    };

    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Recorder Panel */}
                <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 flex flex-col items-center justify-center min-h-[300px]">
                    <div className="text-6xl font-mono font-bold text-gray-100 mb-8 tracking-wider">
                        {formatTime(recordingTime)}
                    </div>
                    
                    {/* Visualizer Bar */}
                    <div className="w-64 h-4 bg-gray-900 rounded-full overflow-hidden mb-8 border border-gray-700">
                        <div 
                            className="h-full bg-gradient-to-r from-green-500 to-red-500 transition-all duration-75"
                            style={{ width: `${(volumeLevel / 255) * 100}%` }}
                        ></div>
                    </div>

                    <div className="flex gap-6">
                        {!isRecording ? (
                            <button 
                                onClick={startRecording}
                                className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-500 shadow-lg shadow-red-900/50 flex items-center justify-center transition-all hover:scale-105"
                                title="Start Recording"
                            >
                                <div className="w-6 h-6 bg-white rounded-full"></div>
                            </button>
                        ) : (
                            <button 
                                onClick={stopRecording}
                                className="w-16 h-16 rounded-full bg-gray-700 hover:bg-gray-600 border-2 border-red-500 flex items-center justify-center transition-all hover:scale-105"
                                title="Stop Recording"
                            >
                                <div className="w-6 h-6 bg-red-500 rounded sm"></div>
                            </button>
                        )}
                    </div>
                    <div className="mt-4 text-sm text-gray-500">
                        {isRecording ? 'REC • Recording Mix...' : 'Ready to record'}
                    </div>
                </div>

                {/* Analysis/Action Panel */}
                <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 flex flex-col">
                    <h3 className="text-lg font-medium text-gray-200 mb-4 flex items-center gap-2">
                        <Icons.Sparkles /> Set Analysis
                    </h3>
                    
                    {!audioBlob && !analysisReport && (
                        <div className="flex-1 flex items-center justify-center text-gray-500 text-center p-8 border border-dashed border-gray-700 rounded-lg">
                            Record a set to generate analysis report.
                        </div>
                    )}

                    {audioBlob && !analysisReport && (
                        <div className="flex-1 flex flex-col items-center justify-center p-8">
                            <div className="mb-4 text-green-400 font-medium">Recording saved successfully!</div>
                            <button 
                                onClick={analyzeRecording} 
                                disabled={isAnalyzing}
                                className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded font-bold w-full transition-colors"
                            >
                                {isAnalyzing ? 'Analyzing Audio (Simulated)...' : 'Analyze Set Quality'}
                            </button>
                        </div>
                    )}

                    {analysisReport && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-gray-900 p-3 rounded border border-gray-700 text-center">
                                    <div className="text-xs text-gray-500 uppercase">Transition Score</div>
                                    <div className={`text-2xl font-bold ${analysisReport.transitionScore > 85 ? 'text-green-400' : 'text-yellow-400'}`}>
                                        {analysisReport.transitionScore}/100
                                    </div>
                                </div>
                                <div className="bg-gray-900 p-3 rounded border border-gray-700 text-center">
                                    <div className="text-xs text-gray-500 uppercase">BPM Accuracy</div>
                                    <div className="text-2xl font-bold text-blue-400">
                                        {analysisReport.bpmAccuracy}%
                                    </div>
                                </div>
                            </div>

                            <div className="bg-gray-900 p-3 rounded border border-gray-700">
                                <div className="text-xs text-gray-500 uppercase mb-2">Energy Flow</div>
                                <div className="flex items-end gap-1 h-16">
                                    {analysisReport.energyGraph.map((val: number, i: number) => (
                                        <div 
                                            key={i} 
                                            className="flex-1 bg-purple-500/50 hover:bg-purple-400" 
                                            style={{ height: `${val}%` }}
                                        ></div>
                                    ))}
                                </div>
                            </div>

                            <div className="bg-gray-900 p-3 rounded border border-gray-700">
                                <div className="text-xs text-gray-500 uppercase mb-2">Detected Tracklist</div>
                                <div className="text-sm space-y-1 max-h-32 overflow-y-auto">
                                    {analysisReport.detectedTracks.map((track: any, i: number) => (
                                        <div key={i} className="flex justify-between text-gray-300">
                                            <span className="font-mono text-gray-500 mr-2">{track.time}</span>
                                            <span className="truncate">{track.artist} - {track.title}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
