
import { AudioFile, ID3Tags } from '../types';

export interface DuplicateGroup {
  id: string;
  key: string; // Wartość, która spowodowała złączenie (np. nazwa, hash, artysta+tytuł)
  files: AudioFile[];
  type: 'filename' | 'metadata' | 'size_duration';
}

const generateId = () => Math.random().toString(36).substr(2, 9);

/**
 * Normalizuje ciąg znaków do porównania (małe litery, bez znaków specjalnych)
 */
const normalize = (str?: string) => {
  if (!str) return '';
  return str.toLowerCase().trim().replace(/[^a-z0-9]/g, '');
};

/**
 * Znajduje duplikaty w liście plików.
 */
export const findDuplicates = (files: AudioFile[]): DuplicateGroup[] => {
  const groups: DuplicateGroup[] = [];
  const processedIds = new Set<string>();

  // 1. Grupowanie po dokładnej nazwie pliku (jeśli są w różnych folderach)
  const nameMap = new Map<string, AudioFile[]>();
  files.forEach(f => {
    const key = f.file.name.toLowerCase();
    if (!nameMap.has(key)) nameMap.set(key, []);
    nameMap.get(key)?.push(f);
  });

  nameMap.forEach((groupFiles, name) => {
    if (groupFiles.length > 1) {
      groups.push({
        id: generateId(),
        key: `Nazwa pliku: ${name}`,
        files: groupFiles,
        type: 'filename'
      });
      groupFiles.forEach(f => processedIds.add(f.id));
    }
  });

  // 2. Grupowanie po Artysta + Tytuł (Metadane)
  // Rozważamy tylko pliki, które nie zostały jeszcze zgrupowane jako duplikaty nazw
  const metaMap = new Map<string, AudioFile[]>();
  
  files.forEach(f => {
    // if (processedIds.has(f.id)) return; // Opcjonalnie: czy chcemy pokazywać plik w wielu grupach? Zazwyczaj nie.

    const tags = f.fetchedTags || f.originalTags;
    const artist = normalize(tags.artist);
    const title = normalize(tags.title);

    if (artist && title) {
      const key = `${artist}|${title}`;
      if (!metaMap.has(key)) metaMap.set(key, []);
      metaMap.get(key)?.push(f);
    }
  });

  metaMap.forEach((groupFiles, key) => {
    // Filtrujemy pliki, które już trafiły do grup (chyba że chcemy redundancję)
    // Tutaj prosta logika: jeśli grupa ma > 1 plików i przynajmniej jeden nie był jeszcze w grupie "filename"
    const uniqueInThisGroup = groupFiles.filter(f => !processedIds.has(f.id));
    
    // Jeśli mamy duplikaty metadanych, które nie są duplikatami nazw
    if (groupFiles.length > 1 && uniqueInThisGroup.length > 0) {
       // Sprawdźmy czy to nie jest ta sama grupa co wyżej (np. ta sama nazwa i te same tagi)
       const isNewGroup = !groups.some(g => g.files.length === groupFiles.length && g.files.every(gf => groupFiles.some(fg => fg.id === gf.id)));
       
       if (isNewGroup) {
          const [artist, title] = key.split('|');
          groups.push({
            id: generateId(),
            key: `Tagi: ${groupFiles[0].fetchedTags?.artist || groupFiles[0].originalTags.artist} - ${groupFiles[0].fetchedTags?.title || groupFiles[0].originalTags.title}`,
            files: groupFiles,
            type: 'metadata'
          });
          groupFiles.forEach(f => processedIds.add(f.id));
       }
    }
  });
  
  // 3. Rozmiar + Czas trwania (heurystyka dla plików bez tagów)
  // Bardziej ryzykowne, więc oznaczamy jako "size_duration"
  const sizeMap = new Map<string, AudioFile[]>();
  files.forEach(f => {
      // Ignorujemy już znalezione
      if (processedIds.has(f.id)) return;
      
      // Klucz: Rozmiar w bajtach
      const key = `${f.file.size}`;
      if (!sizeMap.has(key)) sizeMap.set(key, []);
      sizeMap.get(key)?.push(f);
  });

  sizeMap.forEach((groupFiles, size) => {
      if (groupFiles.length > 1) {
          groups.push({
              id: generateId(),
              key: `Identyczny rozmiar: ${(parseInt(size) / 1024 / 1024).toFixed(2)} MB`,
              files: groupFiles,
              type: 'size_duration'
          });
      }
  });

  return groups;
};
