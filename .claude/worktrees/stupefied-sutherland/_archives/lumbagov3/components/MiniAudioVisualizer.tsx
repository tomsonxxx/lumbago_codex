
import React from 'react';

interface MiniAudioVisualizerProps {
  isPlaying: boolean;
}

const MiniAudioVisualizer: React.FC<MiniAudioVisualizerProps> = ({ isPlaying }) => {
  // Generujemy 12 słupków dla symulacji fali
  const bars = Array.from({ length: 12 }, (_, i) => i);

  return (
    <div className="flex items-end gap-[2px] h-4 mt-1" aria-hidden="true">
      {bars.map((i) => (
        <div
          key={i}
          className={`w-[3px] bg-indigo-500 dark:bg-indigo-400 rounded-t-sm transition-all duration-300 ${
            isPlaying ? 'animate-music-bar' : 'h-[3px]'
          }`}
          style={{
            height: isPlaying ? undefined : '3px',
            animationDelay: isPlaying ? `${Math.random() * 0.5}s` : '0s',
            // Losowa wysokość maksymalna dla każdego słupka, aby wyglądało to naturalnie
            animationDuration: `${0.6 + Math.random() * 0.4}s` 
          }}
        ></div>
      ))}
      <style>{`
        @keyframes music-bar {
          0%, 100% { height: 20%; }
          50% { height: 90%; }
        }
        .animate-music-bar {
          animation: music-bar infinite ease-in-out;
        }
      `}</style>
    </div>
  );
};

export default MiniAudioVisualizer;
