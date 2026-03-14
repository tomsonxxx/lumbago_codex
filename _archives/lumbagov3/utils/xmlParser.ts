
export interface ExternalTrack {
  Artist?: string;
  Title?: string;
  Album?: string;
  TotalTime?: string;
  Location?: string; // file path
}

export interface ExternalPlaylist {
  Name: string;
  Tracks: ExternalTrack[];
}

export interface ParsedLibrary {
  program: 'Rekordbox' | 'VirtualDJ' | 'Unknown';
  version?: string;
  tracks: ExternalTrack[];
  playlists: ExternalPlaylist[];
}

export const parseRekordboxXML = (xmlText: string): ParsedLibrary => {
  const parser = new DOMParser();
  const xmlDoc = parser.parseFromString(xmlText, "text/xml");
  
  const djPlaylists = xmlDoc.getElementsByTagName("DJ_PLAYLISTS")[0];
  const collection = xmlDoc.getElementsByTagName("COLLECTION")[0];
  
  if (!collection) throw new Error("Nieprawidłowy format Rekordbox XML: Brak sekcji COLLECTION");

  const tracksMap = new Map<string, ExternalTrack>();
  const tracks: ExternalTrack[] = [];

  // Parse Tracks
  const trackNodes = collection.getElementsByTagName("TRACK");
  for (let i = 0; i < trackNodes.length; i++) {
    const node = trackNodes[i];
    const id = node.getAttribute("TrackID");
    const track: ExternalTrack = {
      Artist: node.getAttribute("Artist") || undefined,
      Title: node.getAttribute("Name") || undefined,
      Album: node.getAttribute("Album") || undefined,
      TotalTime: node.getAttribute("TotalTime") || undefined,
      Location: node.getAttribute("Location") || undefined,
    };
    if (id) tracksMap.set(id, track);
    tracks.push(track);
  }

  // Parse Playlists (Simplified - flattened)
  const playlists: ExternalPlaylist[] = [];
  const playlistNodes = xmlDoc.getElementsByTagName("NODE"); // Rekordbox uses NODE for folders/playlists
  
  // Funkcja rekurencyjna do wyciągania playlist z drzewa
  const traverseNodes = (nodes: HTMLCollectionOf<Element>) => {
      for(let i=0; i<nodes.length; i++) {
          const node = nodes[i];
          const type = node.getAttribute("Type");
          if (type === "1") { // Playlist
              const name = node.getAttribute("Name") || "Bez nazwy";
              const trackKeys = node.getElementsByTagName("TRACK");
              const plTracks: ExternalTrack[] = [];
              for(let j=0; j<trackKeys.length; j++) {
                  const key = trackKeys[j].getAttribute("Key");
                  if (key && tracksMap.has(key)) {
                      plTracks.push(tracksMap.get(key)!);
                  }
              }
              playlists.push({ Name: name, Tracks: plTracks });
          } else if (type === "0") { // Folder
              traverseNodes(node.children);
          }
      }
  }
  
  // Start from root playlists node
  if (djPlaylists) traverseNodes(djPlaylists.children);

  return {
    program: 'Rekordbox',
    version: xmlDoc.getElementsByTagName("DJ_PLAYLISTS")[0]?.getAttribute("Version") || undefined,
    tracks,
    playlists
  };
};

export const parseVirtualDJXML = (xmlText: string): ParsedLibrary => {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlText, "text/xml");
    
    if (!xmlDoc.getElementsByTagName("VirtualDJ_Database")[0]) {
         throw new Error("To nie wygląda na bazę VirtualDJ.");
    }

    const tracks: ExternalTrack[] = [];
    const songNodes = xmlDoc.getElementsByTagName("Song");
    
    for(let i=0; i<songNodes.length; i++) {
        const node = songNodes[i];
        tracks.push({
            Location: node.getAttribute("FilePath") || undefined,
            Artist: node.getAttribute("Author") || undefined,
            Title: node.getAttribute("Title") || undefined,
            // VDJ trzyma tagi w pod-węźle Tags, ale podstawy są w atrybutach
        });
    }

    // VDJ playlists are usually separate .m3u files or internal history, 
    // XML export structure varies. Basic support for now.
    
    return {
        program: 'VirtualDJ',
        tracks,
        playlists: [] 
    };
}

export const detectAndParseXML = (file: File): Promise<ParsedLibrary> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target?.result as string;
            try {
                if (text.includes('DJ_PLAYLISTS')) {
                    resolve(parseRekordboxXML(text));
                } else if (text.includes('VirtualDJ_Database')) {
                    resolve(parseVirtualDJXML(text));
                } else {
                    reject(new Error("Nie rozpoznano formatu pliku (obsługiwane: Rekordbox, VirtualDJ)."));
                }
            } catch (err) {
                reject(err);
            }
        };
        reader.onerror = () => reject(new Error("Błąd odczytu pliku."));
        reader.readAsText(file);
    });
};