import { AudioFile, Playlist } from '../types';
import { generatePath } from './filenameUtils';

export const generateM3U8 = (playlist: Playlist, allFiles: AudioFile[], relative: boolean = false): string => {
  let content = '#EXTM3U\n';

  const playlistFiles = playlist.trackIds
    .map(id => allFiles.find(f => f.id === id))
    .filter((f): f is AudioFile => !!f);

  playlistFiles.forEach(file => {
    const tags = file.fetchedTags || file.originalTags;
    const duration = file.duration || -1;
    const artist = tags.artist || 'Unknown Artist';
    const title = tags.title || file.file.name;
    
    // EXTINF:duration,Artist - Title
    content += `#EXTINF:${Math.round(duration)},${artist} - ${title}\n`;
    
    // Path
    // Jeśli mamy handle (File System Access), możemy spróbować odtworzyć ścieżkę (jeśli została zapisana)
    // W przeglądarce, bez dostępu do pełnej ścieżki absolutnej, używamy nazwy pliku lub relatywnej
    const path = relative 
        ? file.file.name 
        : (file.webkitRelativePath || file.file.name);
        
    content += `${path}\n`;
  });

  return content;
};

export const downloadPlaylist = (playlist: Playlist, allFiles: AudioFile[]) => {
    const content = generateM3U8(playlist, allFiles);
    const blob = new Blob([content], { type: 'audio/x-mpegurl' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `${playlist.name}.m3u8`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};