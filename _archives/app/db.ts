import Dexie, { Table } from 'dexie';

export interface Track {
  id?: number;
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
  format: string;
  dateAdded: number;
}

// Initialize Dexie as an instance with intersection type for table definitions
// This avoids the "Property 'version' does not exist on type 'MusicDatabase'" TypeScript error
const db = new Dexie('LumbagoMusicDB') as Dexie & {
  tracks: Table<Track, number>;
};

db.version(1).stores({
  tracks: '++id, path, title, artist, album, genre, format' // Indexed fields
});

export { db };