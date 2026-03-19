import { AudioFile, ID3Tags, ProcessingState } from '../types';

// Function to safely format a value for CSV, handling commas, quotes, and newlines.
const formatCsvCell = (value: string | number | undefined | null): string => {
    if (value === undefined || value === null) {
        return '""';
    }
    let str = String(value);
    // If the string contains a comma, a double quote, or a newline, it needs to be quoted.
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        // Escape double quotes by doubling them
        str = str.replace(/"/g, '""');
        return `"${str}"`;
    }
    // It's often safer to just quote everything to be consistent.
    return `"${str}"`;
};

const getStatusText = (state: ProcessingState): string => {
    switch (state) {
        case ProcessingState.PENDING: return 'Oczekuje';
        case ProcessingState.PROCESSING: return 'Przetwarzanie';
        case ProcessingState.DOWNLOADING: return 'Pobieranie';
        case ProcessingState.SUCCESS: return 'Sukces';
        case ProcessingState.ERROR: return 'Błąd';
        default: return 'Nieznany';
    }
}

export const exportFilesToCsv = (files: AudioFile[]): string => {
    const headers = [
        'Oryginalna nazwa pliku',
        'Nowa nazwa pliku',
        'Status',
        'Komunikat o błędzie',
        'Tytuł',
        'Artysta',
        'Artysta albumu',
        'Album',
        'Rok',
        'Gatunek',
        'Numer utworu',
        'Numer dysku',
        'Kompozytor',
        'Oryginalny artysta',
        'Prawa autorskie',
        'Zakodowane przez',
        'Nastrój',
        'Komentarze',
        'URL Okładki',
        'Bitrate (kbps)',
        'Częstotliwość próbkowania (Hz)',
    ];

    const rows = files.map(file => {
        const tags: ID3Tags = file.fetchedTags || {};
        return [
            file.file.name,
            file.newName || '',
            getStatusText(file.state),
            file.errorMessage || '',
            tags.title || '',
            tags.artist || '',
            tags.albumArtist || '',
            tags.album || '',
            tags.year || '',
            tags.genre || '',
            tags.trackNumber || '',
            tags.discNumber || '',
            tags.composer || '',
            tags.originalArtist || '',
            tags.copyright || '',
            tags.encodedBy || '',
            tags.mood || '',
            tags.comments || '',
            tags.albumCoverUrl || '',
            tags.bitrate || '',
            tags.sampleRate || '',
        ].map(formatCsvCell).join(',');
    });

    // Add BOM for Excel to recognize UTF-8 characters correctly
    const csvContent = '\uFEFF' + headers.join(',') + '\n' + rows.join('\n');

    return csvContent;
};
