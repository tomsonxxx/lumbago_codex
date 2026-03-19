import { ID3Tags } from '../types';

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatDate = (timestamp: number): string => {
  return new Date(timestamp).toLocaleString('pl-PL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

interface FilenameAnalysis {
  pattern: string;
  artist?: string;
  title?: string;
  trackNumber?: string;
  confidence: 'High' | 'Medium' | 'Low';
}

/**
 * Heurystyczna analiza nazwy pliku w celu wyodrębnienia metadanych
 * bez użycia tagów ID3.
 */
export const analyzeFilename = (filename: string): FilenameAnalysis => {
  // Usuń rozszerzenie
  const name = filename.substring(0, filename.lastIndexOf('.'));
  
  // Wzorce Regex (kolejność ma znaczenie - od najbardziej szczegółowych)
  
  // 1. "01 - Artist - Title" lub "01. Artist - Title"
  const trackArtistTitle = /^(\d+)[\s.\-_]+(.+?)[\s.\-_]+(.+)$/;
  
  // 2. "Artist - Title"
  const artistTitle = /^(.+?)\s+-\s+(.+)$/;
  
  // 3. "01 Title" (częste w folderach albumów)
  const trackTitle = /^(\d+)[\s.\-_]+(.+)$/;

  const match1 = name.match(trackArtistTitle);
  if (match1) {
    return {
      pattern: 'Track - Artist - Title',
      trackNumber: match1[1],
      artist: match1[2].trim(),
      title: match1[3].trim(),
      confidence: 'High'
    };
  }

  const match2 = name.match(artistTitle);
  if (match2) {
    return {
      pattern: 'Artist - Title',
      artist: match2[1].trim(),
      title: match2[2].trim(),
      confidence: 'Medium'
    };
  }
  
  const match3 = name.match(trackTitle);
  if (match3) {
    return {
      pattern: 'Track - Title',
      trackNumber: match3[1],
      title: match3[2].trim(),
      confidence: 'Medium'
    };
  }

  return {
    pattern: 'Nieznany wzorzec',
    title: name,
    confidence: 'Low'
  };
};