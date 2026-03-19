import React from 'react';

interface AlbumCoverModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string | null;
}

const AlbumCoverModal: React.FC<AlbumCoverModalProps> = ({ isOpen, onClose, imageUrl }) => {
  if (!isOpen || !imageUrl) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-80 flex justify-center items-center z-50 transition-opacity duration-300"
      aria-modal="true"
      role="dialog"
      onClick={onClose}
    >
      <div
        className="relative max-w-3xl max-h-[90vh] p-4 transform transition-all duration-300 scale-95 opacity-0 animate-fade-in-scale"
        onClick={(e) => e.stopPropagation()}
      >
        <img src={imageUrl} alt="Powiększona okładka albumu" className="max-w-full max-h-full object-contain rounded-lg shadow-2xl" />
        <button
          onClick={onClose}
          className="absolute -top-2 -right-2 h-10 w-10 bg-white/20 dark:bg-black/20 text-white rounded-full flex items-center justify-center hover:bg-white/40 dark:hover:bg-black/40 backdrop-blur-sm transition-colors focus:outline-none focus:ring-2 focus:ring-white"
          aria-label="Zamknij"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
       <style>{`
        @keyframes fade-in-scale {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
        .animate-fade-in-scale {
          animation: fade-in-scale 0.2s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default AlbumCoverModal;
