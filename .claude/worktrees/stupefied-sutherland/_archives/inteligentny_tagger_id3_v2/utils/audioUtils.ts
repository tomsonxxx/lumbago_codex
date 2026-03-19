

// Fix: Provide full implementation for audio utility functions.
import { ID3Tags, AudioFile, ProcessingState, Hotcue, CueData } from '../types';

// Assume jsmediatags is loaded globally via a <script> tag
declare const jsmediatags: any;
// Assume ID3Writer is loaded globally via a <script> tag (for MP3)
declare const ID3Writer: any;
// Assume mp4TagWriter is loaded globally via a <script> tag (for M4A/MP4)
declare const mp4TagWriter: any;

const CUE_DATA_PREFIX = 'LUMBAGO_CUES::';


/**
 * Checks if writing tags is supported for a given file type.
 * MP3 support is provided by 'js-id3-writer'.
 * M4A/MP4 support is provided by 'mp4-tag-writer'.
 * @param file The file to check.
 * @returns True if tag writing is supported, false otherwise.
 */
export const isTagWritingSupported = (file: File): boolean => {
    const supportedMimeTypes = [
        'audio/mpeg', // MP3
        'audio/mp3',
        'audio/mp4',  // M4A / MP4
        'audio/x-m4a'
    ];
    return supportedMimeTypes.includes(file.type);
};

export const readID3Tags = (file: File): Promise<{ tags: ID3Tags; hotcues: Hotcue[] }> => {
  return new Promise((resolve) => {
    // WAV files do not use ID3 tags in a way that jsmediatags can read.
    // We'll skip them to avoid errors and return empty tags.
    const fileType = file.type.toLowerCase();
    if (fileType === 'audio/wav' || fileType === 'audio/x-wav') {
        console.warn(`Odczyt tagów nie jest obsługiwany dla plików WAV (${file.name}). Plik zostanie dodany bez metadanych.`);
        return resolve({ tags: {}, hotcues: [] });
    }
      
    if (typeof jsmediatags === 'undefined') {
      console.warn('jsmediatags library not found. Returning empty tags.');
      return resolve({ tags: {}, hotcues: [] });
    }

    jsmediatags.read(file, {
      onSuccess: (tag: any) => {
        const tags: ID3Tags = {};
        let hotcues: Hotcue[] = [];
        const tagData = tag.tags;

        if (tagData.title) tags.title = tagData.title;
        if (tagData.artist) tags.artist = tagData.artist;
        if (tagData.album) tags.album = tagData.album;
        if (tagData.year) tags.year = tagData.year;
        if (tagData.genre) tags.genre = tagData.genre;
        if (tagData.track) tags.trackNumber = tagData.track;

        if (tagData.comment) {
            const commentText = typeof tagData.comment === 'string' ? tagData.comment : tagData.comment.text;
            if (commentText && commentText.startsWith(CUE_DATA_PREFIX)) {
                try {
                    const cueJson = commentText.substring(CUE_DATA_PREFIX.length);
                    const parsedData: CueData = JSON.parse(cueJson);
                    if (parsedData && Array.isArray(parsedData.hotcues)) {
                        hotcues = parsedData.hotcues;
                    }
                } catch (e) {
                    console.warn(`Failed to parse Lumbago cue data from comment: ${e}`);
                    tags.comments = commentText; // Fallback to showing the raw comment
                }
            } else {
                tags.comments = commentText;
            }
        }
        
        if (tagData.TPE2?.data) tags.albumArtist = tagData.TPE2.data;
        else if(tagData.ALBUMARTIST) tags.albumArtist = tagData.ALBUMARTIST;

        if (tagData.TPOS?.data) tags.discNumber = tagData.TPOS.data;
        else if(tagData.DISCNUMBER) tags.discNumber = tagData.DISCNUMBER;
        
        if (tagData.TCOM?.data) tags.composer = tagData.TCOM.data;
        else if(tagData.COMPOSER) tags.composer = tagData.COMPOSER;

        if (tagData.TCOP?.data) tags.copyright = tagData.TCOP.data;
        else if(tagData.COPYRIGHT) tags.copyright = tagData.COPYRIGHT;
        
        if (tagData.TENC?.data) tags.encodedBy = tagData.TENC.data;
        if (tagData.TOPE?.data) tags.originalArtist = tagData.TOPE.data;
        if (tagData.TMOO?.data) tags.mood = tagData.TMOO.data;
        
        if (tagData.picture) {
            const { data, format } = tagData.picture;
            let base64String = "";
            for (let i = 0; i < data.length; i++) {
                base64String += String.fromCharCode(data[i]);
            }
            tags.albumCoverUrl = `data:${format};base64,${window.btoa(base64String)}`;
        }
        
        resolve({ tags, hotcues });
      },
      onError: (error: any) => {
        console.error(`Błąd podczas odczytu tagów z pliku ${file.name}:`, error);
        resolve({ tags: {}, hotcues: [] });
      },
    });
  });
};

const dataURLToArrayBuffer = (dataURL: string) => {
  const base64 = dataURL.split(',')[1];
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
};

export const proxyImageUrl = (url: string | undefined): string | undefined => {
    if (!url || url.startsWith('data:')) return url;
    return `https://corsproxy.io/?${encodeURIComponent(url)}`;
};

const applyID3TagsToFile = async (fileBuffer: ArrayBuffer, tags: ID3Tags, hotcues: Hotcue[]): Promise<ArrayBuffer> => {
    if (typeof ID3Writer === 'undefined') throw new Error("Biblioteka do zapisu tagów MP3 (ID3Writer) nie została załadowana.");
    const writer = new ID3Writer(fileBuffer);

    if (tags.title) writer.setFrame('TIT2', tags.title);
    if (tags.artist) writer.setFrame('TPE1', [tags.artist]);
    if (tags.album) writer.setFrame('TALB', tags.album);
    if (tags.year) writer.setFrame('TYER', tags.year);
    if (tags.genre) writer.setFrame('TCON', [tags.genre]);
    if (tags.trackNumber) writer.setFrame('TRCK', tags.trackNumber);
    if (tags.albumArtist) writer.setFrame('TPE2', [tags.albumArtist]);
    if (tags.mood) writer.setFrame('TMOO', tags.mood);
    
    let commentText = tags.comments || '';
    if (hotcues.length > 0) {
        const cueData: CueData = { hotcues };
        commentText = CUE_DATA_PREFIX + JSON.stringify(cueData);
    }
    writer.setFrame('COMM', { description: '', text: commentText });

    if (tags.composer) writer.setFrame('TCOM', [tags.composer]);
    if (tags.copyright) writer.setFrame('TCOP', tags.copyright);
    if (tags.encodedBy) writer.setFrame('TENC', tags.encodedBy);
    if (tags.originalArtist) writer.setFrame('TOPE', [tags.originalArtist]);
    if (tags.discNumber) writer.setFrame('TPOS', tags.discNumber);
    
    if (tags.albumCoverUrl) {
        try {
            const proxiedUrl = proxyImageUrl(tags.albumCoverUrl);
            const response = await fetch(proxiedUrl!);
            if (!response.ok) throw new Error(`Nie udało się pobrać okładki: ${response.statusText}`);
            const coverBuffer = await response.arrayBuffer();
            writer.setFrame('APIC', { type: 3, data: coverBuffer, description: 'Cover' });
        } catch (error) {
            console.warn(`Nie można przetworzyć okładki albumu:`, error);
        }
    }

    writer.addTag();
    return writer.arrayBuffer;
};

const applyMP4TagsToFile = async (fileBuffer: ArrayBuffer, tags: ID3Tags, hotcues: Hotcue[]): Promise<ArrayBuffer> => {
    if (typeof mp4TagWriter === 'undefined') throw new Error("Biblioteka do zapisu tagów M4A/MP4 (mp4-tag-writer) nie została załadowana.");
    const writer = mp4TagWriter.create(fileBuffer);
    
    if (tags.title) writer.setTag('©nam', tags.title);
    if (tags.artist) writer.setTag('©ART', tags.artist);
    if (tags.album) writer.setTag('©alb', tags.album);
    if (tags.year) writer.setTag('©day', tags.year);
    if (tags.genre) writer.setTag('©gen', tags.genre);

    let commentText = tags.comments || '';
    if (hotcues.length > 0) {
        const cueData: CueData = { hotcues };
        commentText = CUE_DATA_PREFIX + JSON.stringify(cueData);
    }
    writer.setTag('©cmt', commentText);
    
    if (tags.albumArtist) writer.setTag('aART', tags.albumArtist);
    if (tags.composer) writer.setTag('©wrt', tags.composer);
    if (tags.copyright) writer.setTag('cprt', tags.copyright);
    if (tags.encodedBy) writer.setTag('©enc', tags.encodedBy);

    if (tags.trackNumber) {
        const parts = String(tags.trackNumber).split('/');
        writer.setTag('trkn', [parseInt(parts[0], 10) || 0, parts.length > 1 ? parseInt(parts[1], 10) : 0]);
    }
     if (tags.discNumber) {
        const parts = String(tags.discNumber).split('/');
        writer.setTag('disk', [parseInt(parts[0], 10) || 0, parts.length > 1 ? parseInt(parts[1], 10) : 0]);
    }
    
    if (tags.albumCoverUrl) {
         try {
            const proxiedUrl = proxyImageUrl(tags.albumCoverUrl);
            const response = await fetch(proxiedUrl!);
            if (!response.ok) throw new Error(`Nie udało się pobrać okładki: ${response.statusText}`);
            const coverBuffer = await response.arrayBuffer();
            writer.setTag('covr', coverBuffer);
        } catch (error) {
            console.warn(`Nie można przetworzyć okładki albumu dla M4A:`, error);
        }
    }

    return writer.write();
};

export const applyTags = async (file: File, tags: ID3Tags, hotcues: Hotcue[]): Promise<Blob> => {
    if (!isTagWritingSupported(file)) {
        throw new Error(`Zapis tagów dla typu pliku '${file.type}' nie jest obsługiwany.`);
    }

    const fileBuffer = await file.arrayBuffer();
    let taggedBuffer: ArrayBuffer;

    const fileType = file.type;
    if (fileType === 'audio/mpeg' || fileType === 'audio/mp3') {
        taggedBuffer = await applyID3TagsToFile(fileBuffer, tags, hotcues);
    } else if (fileType === 'audio/mp4' || fileType === 'audio/x-m4a') {
        taggedBuffer = await applyMP4TagsToFile(fileBuffer, tags, hotcues);
    } else {
        throw new Error(`Nieoczekiwany typ pliku: ${fileType}`);
    }
    
    return new Blob([taggedBuffer], { type: file.type });
};

export const saveFileDirectly = async (
  dirHandle: any,
  audioFile: AudioFile
): Promise<{ success: boolean; updatedFile?: AudioFile; errorMessage?: string }> => {
  try {
    const supportsTagWriting = isTagWritingSupported(audioFile.file);
    if (!audioFile.handle) throw new Error("Brak referencji do pliku (file handle).");
    
    let blobToSave: Blob = audioFile.file;
    let performedTagWrite = false;

    if (supportsTagWriting && (audioFile.fetchedTags || audioFile.hotcues.length > 0)) {
      try {
        blobToSave = await applyTags(audioFile.file, audioFile.fetchedTags || audioFile.originalTags, audioFile.hotcues);
        performedTagWrite = true;
      } catch (tagError) {
        console.warn(`Nie udało się zapisać tagów dla ${audioFile.file.name}, plik zostanie tylko przemianowany. Błąd:`, tagError);
        blobToSave = audioFile.file;
      }
    }

    const needsRename = audioFile.newName && audioFile.newName !== audioFile.webkitRelativePath;
    if (!needsRename && !performedTagWrite) return { success: true, updatedFile: audioFile };

    if (needsRename) {
      const newPath = audioFile.newName!;
      const pathParts = newPath.split('/').filter(p => p && p !== '.');
      const filename = pathParts.pop();
      if (!filename) throw new Error(`Wygenerowana nazwa pliku jest nieprawidłowa: ${newPath}`);

      let currentDirHandle = dirHandle;
      for (const part of pathParts) {
        currentDirHandle = await currentDirHandle.getDirectoryHandle(part, { create: true });
      }
      
      const newHandle = await currentDirHandle.getFileHandle(filename, { create: true });
      const writable = await newHandle.createWritable();
      await writable.write(blobToSave);
      await writable.close();
      
      try {
        const originalPath = audioFile.webkitRelativePath;
        if (originalPath && originalPath !== newPath) {
             const originalPathParts = originalPath.split('/').filter(p => p);
             const originalFilename = originalPathParts.pop();
             if (originalFilename) {
                let parentDirHandle = dirHandle;
                for (const part of originalPathParts) {
                    parentDirHandle = await parentDirHandle.getDirectoryHandle(part, { create: false });
                }
                await parentDirHandle.removeEntry(originalFilename);
             }
        }
      } catch(removeError: any) {
         console.warn(`Nowy plik został pomyślnie zapisany w '${newPath}', ale nie udało się usunąć oryginalnego pliku '${audioFile.webkitRelativePath}'. Błąd:`, removeError);
      }

      const newFile = await newHandle.getFile();
      return { 
        success: true, 
        updatedFile: { 
            ...audioFile, 
            file: newFile, 
            handle: newHandle, 
            newName: newPath,
            webkitRelativePath: newPath
        }
      };
    
    } else if (performedTagWrite) {
      const writable = await audioFile.handle.createWritable({ keepExistingData: false });
      await writable.write(blobToSave);
      await writable.close();
      
      const updatedCoreFile = await audioFile.handle.getFile();
      return { 
        success: true, 
        updatedFile: { ...audioFile, file: updatedCoreFile }
      };
    }

    return { success: true, updatedFile: audioFile };

  } catch (err: any) {
    console.error(`Nie udało się zapisać pliku ${audioFile.file.name}:`, err);
    return { success: false, errorMessage: err.message || "Wystąpił nieznany błąd zapisu." };
  }
};