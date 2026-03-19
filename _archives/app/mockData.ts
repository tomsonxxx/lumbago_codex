
export interface MockTrack {
  id: string;
  path: string;
  title: string;
  artist: string;
  album: string;
  genre: string;
  year: string;
  bpm: number;
  key: string;
  duration: number;
  fileSize: number;
  fingerprint: string;
  hash: string;
}

export const mockFileDatabase: MockTrack[] = [
  { id: '1', path: '/source/Deep_House/track1.mp3', title: 'Track 1', artist: 'Artist A', album: 'Album X', genre: 'Deep House', year: '2023', bpm: 124, key: 'Am', duration: 240, fileSize: 5000000, fingerprint: 'fp123A', hash: 'h123A' },
  { id: '2', path: '/source/Techno/track2.flac', title: 'Track 2', artist: 'Artist B', album: 'Album Y', genre: 'Techno', year: '2022', bpm: 130, key: 'G#m', duration: 300, fileSize: 25000000, fingerprint: 'fp123B', hash: 'h123B' },
  { id: '3', path: '/source/Deep_House/track3.wav', title: 'Track 3', artist: 'Artist C', album: 'Album X', genre: 'Deep House', year: '2023', bpm: 125, key: 'Am', duration: 250, fileSize: 40000000, fingerprint: 'fp123C', hash: 'h123C' },
  { id: '4', path: '/source/Oldies/track4.mp3', title: 'Track 4', artist: 'Artist D', album: 'Album Z', genre: 'Pop', year: '1995', bpm: 100, key: 'C', duration: 180, fileSize: 3000000, fingerprint: 'fp123D', hash: 'h123D' },
  { id: '5', path: '/source/Techno/sub/track5.mp3', title: 'Track 5', artist: 'Artist E', album: 'Album Y', genre: 'Techno', year: '2022', bpm: 132, key: 'G#m', duration: 320, fileSize: 6000000, fingerprint: 'fp123E', hash: 'h123E' },
  // Additional paths for better simulation
  { id: '6', path: '/MyMusic/Downloads/track1_copy.mp3', title: 'Track 1', artist: 'Artist A', album: 'Album X', genre: 'Deep House', year: '2023', bpm: 124, key: 'Am', duration: 240, fileSize: 5000000, fingerprint: 'fp123A', hash: 'h123A' },
  { id: '7', path: '/Users/DJ/Music/Deep_House/track1_alt_mix.mp3', title: 'Track 1 (Alt Mix)', artist: 'Artist A', album: 'Album X', genre: 'Deep House', year: '2023', bpm: 124, key: 'Am', duration: 245, fileSize: 5100000, fingerprint: 'fp123B', hash: 'h123B' },
  { id: '8', path: '/External/USB/track1_master.mp3', title: 'Track 1', artist: 'Artist A', album: 'Album X', genre: 'Deep House', year: '2023', bpm: 124, key: 'Am', duration: 240, fileSize: 5000000, fingerprint: 'fp123A', hash: 'h123A' },
  { id: '9', path: '/MyMusic/Jazz/smooth.aac', title: 'Smooth Jazz', artist: 'Jazz Band', album: 'Smooth', genre: 'Jazz', year: '2020', bpm: 90, key: 'C', duration: 200, fileSize: 4000000, fingerprint: 'fpJazz', hash: 'hJazz' },
  { id: '10', path: '/Audiophile/HighRes/symphony.dsf', title: 'Symphony No. 5', artist: 'Orchestra', album: 'Classics', genre: 'Classical', year: '2019', bpm: 80, key: 'Cm', duration: 600, fileSize: 100000000, fingerprint: 'fpClassic', hash: 'hClassic' },
  { id: '11', path: '/Studio/Projects/beat.aiff', title: 'Beat 1', artist: 'Producer', album: 'Beats', genre: 'Hip Hop', year: '2024', bpm: 95, key: 'Fm', duration: 150, fileSize: 20000000, fingerprint: 'fpBeat', hash: 'hBeat' },
  { id: '12', path: '/C:/Music/test.mp3', title: 'Windows Test', artist: 'Win', album: 'OS', genre: 'System', year: '2021', bpm: 120, key: 'C', duration: 100, fileSize: 1000, fingerprint: 'fpWin', hash: 'hWin' },
];

export interface MockRecognitionResult {
  id: string;
  title: string;
  artist: string;
  album: string;
  genre: string;
  year: string;
  source: string;
  confidence: number;
  artworkUrl?: string;
}

export const mockExternalDBResults: MockRecognitionResult[] = [
  { id: 'ext1', title: 'Track 1', artist: 'Artist A', album: 'Album X', genre: 'Deep House', year: '2023', source: 'MusicBrainz', confidence: 0.98, artworkUrl: 'https://via.placeholder.com/150/0000FF/FFFFFF?text=AlbumX' },
  { id: 'ext2', title: 'Track 1 (Remix)', artist: 'Artist A', album: 'Album X - Remixes', genre: 'Deep House', year: '2024', source: 'Discogs', confidence: 0.85, artworkUrl: 'https://via.placeholder.com/150/FF0000/FFFFFF?text=Remixes' },
  { id: 'ext3', title: 'Track 2', artist: 'Artist B', album: 'Album Y', genre: 'Techno', year: '2022', source: 'AcoustID', confidence: 0.95, artworkUrl: 'https://via.placeholder.com/150/00FF00/FFFFFF?text=AlbumY' },
  { id: 'ext4', title: 'Sunrise Groove', artist: 'Various Artists', album: 'Chillout Sessions Vol. 5', genre: 'Chillout', year: '2023', source: 'MusicBrainz', confidence: 0.90, artworkUrl: 'https://via.placeholder.com/150/FFFF00/000000?text=Chillout' },
];
