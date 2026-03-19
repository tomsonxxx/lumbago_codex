
import { ID3Tags, AudioFile, ProcessingState } from '../types';

// Assume jsmediatags is loaded globally via a <script> tag
declare const jsmediatags: any;
// Assume ID3Writer is loaded globally via a <script> tag (for MP3)
declare const ID3Writer: any;
// Assume mp4TagWriter is loaded globally via a <script> tag (for M4A/MP4)
declare const mp4TagWriter: any;


/**
 * Checks if writing tags is supported for a given file type.
 * MP3 support is provided by 'browser-id3-writer'.
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

export const readID3Tags = (file: File): Promise<ID3Tags> => {
  return new Promise((resolve, reject) => {
    if (typeof jsmediatags === 'undefined') {
      console.warn('jsmediatags library not found. Returning empty tags.');
      return resolve({});
    }
    
    // FIX: Proactively skip reading tags for WAV files. The jsmediatags library
    // does not support the RIFF info chunk format used by WAV files, which causes
    // a 'tagFormat' error. By skipping it, we avoid the error and proceed smoothly.
    const lowerCaseName = file.name.toLowerCase();
    if (file.type.startsWith('audio/wav') || file.type.startsWith('audio/x-wav') || lowerCaseName.endsWith('.wav') || lowerCaseName.endsWith('.wave')) {
        console.log(`Pomijanie odczytu tagów dla pliku WAV (${file.name}), ponieważ format nie jest w pełni obsługiwany przez bibliotekę odczytującą.`);
        return resolve({});
    }

    jsmediatags.read(file, {
      onSuccess: (tag: any) => {
        // jsmediatags attempts to unify tags, so we can check for common properties
        // regardless of the underlying format (ID3, Vorbis comment, MP4 atoms, etc.)
        const tags: ID3Tags = {};
        const tagData = tag.tags;

        // 1. Basic standardized fields (Library usually handles ID3, MP4 and basic Vorbis mapping)
        if (tagData.title) tags.title = tagData.title;
        if (tagData.artist) tags.artist = tagData.artist;
        if (tagData.album) tags.album = tagData.album;
        if (tagData.year) tags.year = tagData.year;
        if (tagData.genre) tags.genre = tagData.genre;

        // Vorbis specific fallbacks for basics
        if (!tags.year && tagData.DATE) tags.year = tagData.DATE; // FLAC often uses DATE

        // 2. Track Number
        if (tagData.track) tags.trackNumber = tagData.track;
        else if (tagData.TRACKNUMBER) tags.trackNumber = tagData.TRACKNUMBER; // Vorbis

        // 3. Comments
        if (tagData.comment) {
             tags.comments = typeof tagData.comment === 'string' ? tagData.comment : tagData.comment.text;
        } else if (tagData.DESCRIPTION) {
             tags.comments = tagData.DESCRIPTION; // Vorbis often uses DESCRIPTION
        } else if (tagData.COMMENT) {
             tags.comments = tagData.COMMENT; // Raw Vorbis comment
        }
        
        // 4. Album Artist
        // TPE2 is ID3, ALBUMARTIST is Vorbis
        if (tagData.TPE2?.data) tags.albumArtist = tagData.TPE2.data;
        else if(tagData.ALBUMARTIST) tags.albumArtist = tagData.ALBUMARTIST;
        else if(tagData['ALBUM ARTIST']) tags.albumArtist = tagData['ALBUM ARTIST']; 

        // 5. Disc Number
        // TPOS is ID3, DISCNUMBER is Vorbis
        if (tagData.TPOS?.data) tags.discNumber = tagData.TPOS.data;
        else if(tagData.DISCNUMBER) tags.discNumber = tagData.DISCNUMBER;
        
        // 6. Composer
        // TCOM is ID3, COMPOSER is Vorbis
        if (tagData.TCOM?.data) tags.composer = tagData.TCOM.data;
        else if(tagData.COMPOSER) tags.composer = tagData.COMPOSER;

        // 7. Copyright
        // TCOP is ID3, COPYRIGHT is Vorbis
        if (tagData.TCOP?.data) tags.copyright = tagData.TCOP.data;
        else if(tagData.COPYRIGHT) tags.copyright = tagData.COPYRIGHT;
        
        // 8. Encoded By
        // TENC is ID3, ENCODEDBY/ENCODER is Vorbis
        if (tagData.TENC?.data) tags.encodedBy = tagData.TENC.data;
        else if (tagData.ENCODEDBY) tags.encodedBy = tagData.ENCODEDBY;
        else if (tagData.ENCODER) tags.encodedBy = tagData.ENCODER;

        // 9. Original Artist
        // TOPE is ID3, ORIGINALARTIST is Vorbis
        if (tagData.TOPE?.data) tags.originalArtist = tagData.TOPE.data;
        else if (tagData.ORIGINALARTIST) tags.originalArtist = tagData.ORIGINALARTIST;

        // 10. Mood
        // TMOO is ID3, MOOD is Vorbis
        if (tagData.TMOO?.data) tags.mood = tagData.TMOO.data; 
        else if (tagData.MOOD) tags.mood = tagData.MOOD;
        
        // Picture (jsmediatags handles parsing METADATA_BLOCK_PICTURE for FLAC as well)
        if (tagData.picture) {
            const { data, format } = tagData.picture;
            let base64String = "";
            for (let i = 0; i < data.length; i++) {
                base64String += String.fromCharCode(data[i]);
            }
            tags.albumCoverUrl = `data:${format};base64,${window.btoa(base64String)}`;
        }
        
        resolve(tags);
      },
      onError: (error: any) => {
        const errorType = error.type || 'Unknown';
        const errorInfo = error.info || 'No additional info';
        console.error(`Błąd podczas odczytu tagów z pliku ${file.name}: Typ błędu: ${errorType}, Info: ${errorInfo}`, error);
        // Resolve with empty tags on error to not block the flow
        resolve({});
      },
    });
  });
};

// Helper to convert base64 data URL to ArrayBuffer
const dataURLToArrayBuffer = (dataURL: string) => {
  try {
    const base64 = dataURL.split(',')[1];
    const binaryString = atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  } catch (e) {
    console.error("Error converting DataURL to ArrayBuffer", e);
    throw new Error("Nieprawidłowy format obrazu okładki.");
  }
};

// Helper function to proxy image URLs to avoid CORS issues
export const proxyImageUrl = (url: string | undefined): string | undefined => {
    if (!url || url.startsWith('data:')) {
        return url;
    }
    return `https://corsproxy.io/?${encodeURIComponent(url)}`;
};


/**
 * Applies tags to an MP3 file using ID3Writer.
 * @param fileBuffer The ArrayBuffer of the MP3 file.
 * @param tags The tags to apply.
 * @returns An ArrayBuffer of the tagged MP3 file.
 */
const applyID3TagsToFile = async (fileBuffer: ArrayBuffer, tags: ID3Tags): Promise<ArrayBuffer> => {
    // FIX: Access the global ID3Writer strictly through window to avoid ReferenceError if not loaded.
    // Do not use 'ID3Writer' as a fallback variable.
    const Writer = (window as any).ID3Writer || (window as any).BrowserID3Writer;

    if (!Writer) {
        throw new Error("Biblioteka do zapisu tagów MP3 (ID3Writer) nie została załadowana. Sprawdź połączenie internetowe lub odśwież stronę.");
    }
    const writer = new Writer(fileBuffer);

    if (tags.title) writer.setFrame('TIT2', tags.title);
    if (tags.artist) writer.setFrame('TPE1', [tags.artist]);
    if (tags.album) writer.setFrame('TALB', tags.album);
    if (tags.year) writer.setFrame('TYER', tags.year);
    if (tags.genre) writer.setFrame('TCON', [tags.genre]);
    if (tags.trackNumber) writer.setFrame('TRCK', tags.trackNumber);
    if (tags.albumArtist) writer.setFrame('TPE2', [tags.albumArtist]);
    if (tags.mood) writer.setFrame('TMOO', tags.mood);
    if (tags.comments) writer.setFrame('COMM', { description: 'Comment', text: tags.comments });
    if (tags.composer) writer.setFrame('TCOM', [tags.composer]);
    if (tags.copyright) writer.setFrame('TCOP', tags.copyright);
    if (tags.encodedBy) writer.setFrame('TENC', tags.encodedBy);
    if (tags.originalArtist) writer.setFrame('TOPE', [tags.originalArtist]);
    if (tags.discNumber) writer.setFrame('TPOS', tags.discNumber);
    
    if (tags.albumCoverUrl) {
        try {
            let coverBuffer: ArrayBuffer;
            if (tags.albumCoverUrl.startsWith('data:')) {
                coverBuffer = dataURLToArrayBuffer(tags.albumCoverUrl);
            } else {
                const proxiedUrl = proxyImageUrl(tags.albumCoverUrl);
                const response = await fetch(proxiedUrl!);
                if (!response.ok) throw new Error(`Nie udało się pobrać okładki: ${response.statusText}`);
                coverBuffer = await response.arrayBuffer();
            }
            writer.setFrame('APIC', {
                type: 3, // 'Cover (front)'
                data: coverBuffer,
                description: 'Cover',
            });
        } catch (error) {
            console.warn(`Nie można przetworzyć okładki albumu z URL: '${tags.albumCoverUrl}'. Błąd:`, error);
        }
    }

    writer.addTag();
    return writer.arrayBuffer;
};

/**
 * Applies tags to an M4A/MP4 file using mp4-tag-writer.
 * @param fileBuffer The ArrayBuffer of the M4A/MP4 file.
 * @param tags The tags to apply.
 * @returns An ArrayBuffer of the tagged M4A/MP4 file.
 */
const applyMP4TagsToFile = async (fileBuffer: ArrayBuffer, tags: ID3Tags): Promise<ArrayBuffer> => {
    // FIX: Access safe check for mp4TagWriter
    const Writer = (window as any).mp4TagWriter || (typeof mp4TagWriter !== 'undefined' ? mp4TagWriter : undefined);

    if (!Writer) {
        throw new Error("Biblioteka do zapisu tagów M4A/MP4 (mp4-tag-writer) nie została załadowana.");
    }
    
    const writer = Writer.create(fileBuffer);
    
    // Map ID3Tags to MP4 atoms
    if (tags.title) writer.setTag('©nam', tags.title);
    if (tags.artist) writer.setTag('©ART', tags.artist);
    if (tags.album) writer.setTag('©alb', tags.album);
    if (tags.year) writer.setTag('©day', tags.year);
    if (tags.genre) writer.setTag('©gen', tags.genre);
    if (tags.comments) writer.setTag('©cmt', tags.comments);
    if (tags.albumArtist) writer.setTag('aART', tags.albumArtist);
    if (tags.composer) writer.setTag('©wrt', tags.composer);
    if (tags.copyright) writer.setTag('cprt', tags.copyright);
    if (tags.encodedBy) writer.setTag('©enc', tags.encodedBy);
    
    // NEW: Add custom tags for 'mood' and 'originalArtist' for better compatibility with iTunes.
    // These are stored in generic "----" atoms with a reverse-DNS mean and a name.
    if (tags.mood) {
        writer.setTag('----', { mean: 'com.apple.iTunes', name: 'MOOD', data: tags.mood });
    }
    if (tags.originalArtist) {
        writer.setTag('----', { mean: 'com.apple.iTunes', name: 'ORIGINAL ARTIST', data: tags.originalArtist });
    }

    // Track and Disc numbers are special cases
    if (tags.trackNumber) {
        const parts = String(tags.trackNumber).split('/');
        const number = parseInt(parts[0], 10) || 0;
        const total = parts.length > 1 ? parseInt(parts[1], 10) : 0;
        writer.setTag('trkn', [number, total]);
    }
     if (tags.discNumber) {
        const parts = String(tags.discNumber).split('/');
        const number = parseInt(parts[0], 10) || 0;
        const total = parts.length > 1 ? parseInt(parts[1], 10) : 0;
        writer.setTag('disk', [number, total]);
    }
    
    if (tags.albumCoverUrl) {
         try {
            let coverBuffer: ArrayBuffer;
            if (tags.albumCoverUrl.startsWith('data:')) {
                coverBuffer = dataURLToArrayBuffer(tags.albumCoverUrl);
            } else {
                const proxiedUrl = proxyImageUrl(tags.albumCoverUrl);
                const response = await fetch(proxiedUrl!);
                if (!response.ok) throw new Error(`Nie udało się pobrać okładki: ${response.statusText}`);
                coverBuffer = await response.arrayBuffer();
            }
            writer.setTag('covr', coverBuffer);
        } catch (error) {
            console.warn(`Nie można przetworzyć okładki albumu dla M4A z URL: '${tags.albumCoverUrl}'. Błąd:`, error);
        }
    }

    return writer.write();
};

/**
 * Applies tags to an audio file, automatically detecting the format (MP3 or M4A/MP4).
 * @param file The original audio file.
 * @param tags The tags to apply.
 * @returns A Blob of the new file with tags applied.
 */
export const applyTags = async (file: File, tags: ID3Tags): Promise<Blob> => {
    if (!isTagWritingSupported(file)) {
        throw new Error(`Zapis tagów dla typu pliku '${file.type}' nie jest obsługiwany.`);
    }

    try {
        const fileBuffer = await file.arrayBuffer();
        let taggedBuffer: ArrayBuffer;

        const fileType = file.type;
        if (fileType === 'audio/mpeg' || fileType === 'audio/mp3') {
            taggedBuffer = await applyID3TagsToFile(fileBuffer, tags);
        } else if (fileType === 'audio/mp4' || fileType === 'audio/x-m4a') {
            taggedBuffer = await applyMP4TagsToFile(fileBuffer, tags);
        } else {
            throw new Error(`Nieoczekiwany typ pliku: ${fileType}`);
        }
        
        return new Blob([taggedBuffer], { type: file.type });
    } catch (error) {
        console.error(`Błąd podczas aplikowania tagów dla pliku ${file.name}:`, error);
        // If tagging fails, return the original file blob so the save process can continue (e.g. renaming)
        // We throw specific error so caller knows tags weren't applied but file is safe
        throw new Error(`Nie udało się zapisać tagów: ${error instanceof Error ? error.message : String(error)}. Plik zostanie zapisany w oryginalnej formie.`);
    }
};


/**
 * Saves a file directly to the user's filesystem using the File System Access API.
 * This is the "brain" for saving, which intelligently decides whether to write tags
 * based on the file format and handles errors robustly.
 * @param dirHandle The handle to the root directory for saving.
 * @param audioFile The file object from the application state.
 * @returns An object indicating success and the updated file object for state management.
 */
export const saveFileDirectly = async (
  dirHandle: any, // FileSystemDirectoryHandle
  audioFile: AudioFile
): Promise<{ success: boolean; updatedFile?: AudioFile; errorMessage?: string }> => {
  try {
    const supportsTagWriting = isTagWritingSupported(audioFile.file);
    
    if (!audioFile.handle) {
      throw new Error("Brak referencji do pliku (file handle). Nie można zapisać, ponieważ plik nie pochodzi z trybu bezpośredniego dostępu.");
    }
    
    let blobToSave: Blob = audioFile.file;
    let tagWriteSuccess = false;
    let tagErrorMsg = "";

    // Intelligent Tag Writing: Only attempt to write tags for supported files.
    // For other formats (like FLAC), we proceed with just renaming/moving.
    if (supportsTagWriting && audioFile.fetchedTags) {
      try {
        blobToSave = await applyTags(audioFile.file, audioFile.fetchedTags);
        tagWriteSuccess = true;
      } catch (tagError: any) {
        console.warn(`Nie udało się zapisać tagów dla ${audioFile.file.name}, plik zostanie tylko przemianowany. Błąd:`, tagError);
        tagErrorMsg = tagError.message;
        // Fallback to original blob if tagging fails
        blobToSave = audioFile.file;
      }
    }

    const currentPath = audioFile.webkitRelativePath || audioFile.file.name;
    const targetPath = audioFile.newName || currentPath;
    
    // Normalize paths to check if rename is actually needed
    const normalizedCurrent = currentPath.replace(/^\/+/, '');
    const normalizedTarget = targetPath.replace(/^\/+/, '');
    
    const needsRename = normalizedCurrent !== normalizedTarget;

    // If no changes are needed (no rename and no tags written), we can skip.
    // Exception: if we WANTED to write tags but failed, we return specific info.
    if (!needsRename && !tagWriteSuccess) {
        if (tagErrorMsg) {
             // If renaming wasn't needed, but tags failed, it's a partial failure.
            return { success: false, errorMessage: `Brak zmiany nazwy i błąd zapisu tagów: ${tagErrorMsg}` };
        }
        // Nothing changed at all, return success.
        return { success: true, updatedFile: audioFile };
    }

    // --- 1. PREPARE TARGET DIRECTORY HANDLE ---
    const pathParts = normalizedTarget.split('/').filter(p => p && p !== '.');
    const filename = pathParts.pop();

    if (!filename) {
        throw new Error(`Wygenerowana nazwa pliku jest nieprawidłowa: ${targetPath}`);
    }

    let targetDirHandle = dirHandle;
    // Iterate through folders to get/create the destination folder
    for (const part of pathParts) {
        try {
            targetDirHandle = await targetDirHandle.getDirectoryHandle(part, { create: true });
        } catch (e: any) {
             if (e.name === 'NotAllowedError') throw new Error(`Brak uprawnień do tworzenia folderu "${part}". Sprawdź uprawnienia przeglądarki.`);
             throw new Error(`Nie udało się utworzyć folderu "${part}": ${e.message}`);
        }
    }
      
    // --- 2. CREATE/WRITE TO TARGET FILE ---
    let newFileHandle;
    try {
        newFileHandle = await targetDirHandle.getFileHandle(filename, { create: true });
    } catch (e: any) {
        if (e.name === 'TypeMismatchError') throw new Error(`Nazwa "${filename}" jest już zajęta przez folder.`);
        if (e.name === 'NotAllowedError') throw new Error(`Brak uprawnień do utworzenia pliku "${filename}".`);
        throw e;
    }

    // Check if we are overwriting the SAME file in place
    try {
        // createWritable might fail if file is locked by another app
        const writable = await newFileHandle.createWritable({ keepExistingData: false });
        await writable.write(blobToSave);
        await writable.close();
    } catch (e: any) {
        if (e.name === 'NotAllowedError' || e.name === 'SecurityError') {
             throw new Error(`Użytkownik odmówił uprawnień do zapisu pliku "${filename}". Upewnij się, że zaakceptowałeś prośbę przeglądarki.`);
        }
        if (e.name === 'InvalidStateError' || e.name === 'NoModificationAllowedError' || e.code === 11) {
             throw new Error(`Plik "${filename}" jest zablokowany lub używany przez inny program (np. odtwarzacz muzyki). Zamknij inne aplikacje i spróbuj ponownie.`);
        }
        if (e.name === 'QuotaExceededError') {
             throw new Error(`Brak miejsca na dysku, aby zapisać plik "${filename}".`);
        }
        throw new Error(`Błąd zapisu danych do pliku "${filename}": ${e.message}`);
    }
    
    // --- 3. CLEANUP OLD FILE (If Rename/Move occurred) ---
    if (needsRename) {
      try {
        const originalPathParts = normalizedCurrent.split('/').filter(p => p);
        const originalFilename = originalPathParts.pop();
             
        if (originalFilename) {
            let parentDirHandle = dirHandle;
            // Navigate to original folder
            for (const part of originalPathParts) {
                try {
                    parentDirHandle = await parentDirHandle.getDirectoryHandle(part, { create: false });
                } catch {
                    // If we can't find the source folder, it might have been moved already or logic is off.
                    // We silently ignore as the new file is safe.
                    parentDirHandle = null;
                    break;
                }
            }
            
            if (parentDirHandle) {
                 await parentDirHandle.removeEntry(originalFilename);
            }
        }
      } catch(removeError: any) {
         // Log a warning but do not treat this as a failure of the entire save operation.
         // The new file has been created successfully. The old file might just need manual cleanup.
         console.warn(`Nowy plik został pomyślnie zapisany w '${targetPath}', ale nie udało się usunąć oryginalnego pliku '${currentPath}'. Może być zablokowany przez inny proces. Błąd:`, removeError);
      }
    }

    // --- 4. RETURN SUCCESS ---
    const updatedCoreFile = await newFileHandle.getFile();
    
    // We construct a detailed success message if tag writing failed but rename worked
    let errorWarning = undefined;
    if (!tagWriteSuccess && supportsTagWriting && audioFile.fetchedTags) {
        errorWarning = "Nazwa zmieniona, ale tagi nie zostały zapisane (problem z biblioteką).";
    }

    return { 
        success: true, 
        errorMessage: errorWarning,
        updatedFile: { 
            ...audioFile, 
            file: updatedCoreFile, 
            handle: newFileHandle, 
            newName: normalizedTarget,
            webkitRelativePath: normalizedTarget // Update the path for future operations
        }
    };

  } catch (err: any) {
    console.error(`Nie udało się zapisać pliku ${audioFile.file.name}:`, err);
    return { success: false, errorMessage: err.message || "Wystąpił nieznany błąd zapisu." };
  }
};
