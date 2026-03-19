import { GenericTrack, CuePoint, Loop, AudioFile } from '../types';

const VDJ_KEY_MAP: Record<string, string> = { 'A#m': '6A', 'Fm': '7A', 'Cm': '8A', 'Gm': '9A', 'Dm': '10A', 'Am': '11A', 'Em': '12A', 'Bm': '1A', 'F#m': '2A', 'C#m': '3A', 'G#m': '4A', 'D#m': '5A', 'C#': '1B', 'G#': '2B', 'D#': '3B', 'A#': '4B', 'F': '5B', 'C': '6B', 'G': '7B', 'D': '8B', 'A': '9B', 'E': '10B', 'B': '11B', 'F#': '12B' };
const RB_KEY_MAP: Record<string, string> = { '1': '8B', '2': '3B', '3': '10B', '4': '5B', '5': '12B', '6': '7B', '7': '2B', '8': '9B', '9': '4B', '10': '11B', '11': '6B', '12': '1B', '13': '8A', '14': '3A', '15': '10A', '16': '5A', '17': '12A', '18': '7A', '19': '2A', '20': '9A', '21': '4A', '22': '11A', '23': '6A', '24': '1A' };
const CAMELOT_TO_RB_KEY: Record<string, string> = Object.fromEntries(Object.entries(RB_KEY_MAP).map(([k, v]) => [v, k]));
const CAMELOT_TO_VDJ_KEY: Record<string, string> = Object.fromEntries(Object.entries(VDJ_KEY_MAP).map(([k, v]) => [v, k]));

const decodeLocation = (location: string): string => {
    try {
        return decodeURIComponent(location.replace('file://localhost/', ''));
    } catch (e) {
        console.warn('Could not decode location:', location, e);
        return location;
    }
}

export const parseRekordboxXml = (xmlDoc: XMLDocument): GenericTrack[] => {
    const tracks: GenericTrack[] = [];
    xmlDoc.querySelectorAll('COLLECTION > TRACK').forEach(node => {
        const cues: CuePoint[] = [];
        const loops: Loop[] = [];
        node.querySelectorAll('POSITION_MARK').forEach(mark => {
            const start = parseFloat(mark.getAttribute('Start') || '0') * 1000;
            const type = parseInt(mark.getAttribute('Type') || '0', 10);
            if (type === 0 || type === 1) { 
                 cues.push({ timeMs: start, name: mark.getAttribute('Name') || `Cue ${cues.length + 1}`, type: type });
            }
            if(type === 3) {
                const end = parseFloat(mark.getAttribute('End') || '0') * 1000;
                if (end > start) loops.push({ startMs: start, endMs: end });
            }
        });
        const rbKey = node.getAttribute('Tonality');
        tracks.push({
            location: decodeLocation(node.getAttribute('Location') || ''),
            title: node.getAttribute('Name') || undefined,
            artist: node.getAttribute('Artist') || undefined,
            album: node.getAttribute('Album') || undefined,
            genre: node.getAttribute('Genre') || undefined,
            year: node.getAttribute('Year') || undefined,
            bpm: parseFloat(node.getAttribute('AverageBpm') || '0'),
            key: rbKey ? (RB_KEY_MAP[rbKey] || rbKey) : undefined,
            rating: parseInt(node.getAttribute('Rating') || '0', 10),
            playCount: parseInt(node.getAttribute('PlayCount') || '0', 10),
            cues,
            loops,
        });
    });
    return tracks;
};

export const parseVirtualDjXml = (xmlDoc: XMLDocument): GenericTrack[] => {
    const tracks: GenericTrack[] = [];
    xmlDoc.querySelectorAll('VirtualDJ_Database > Song').forEach(node => {
        const cues: CuePoint[] = [];
        node.querySelectorAll('Poi').forEach(poi => {
            cues.push({ timeMs: parseInt(poi.getAttribute('Pos') || '0', 10) / 1000, name: poi.getAttribute('Name') || `Cue ${cues.length + 1}`, type: 0 });
        });
        const vdjKey = node.querySelector('Key')?.textContent;
        tracks.push({
            location: node.getAttribute('FilePath') || '',
            title: node.querySelector('Title')?.textContent || undefined,
            artist: node.querySelector('Artist')?.textContent || undefined,
            album: node.querySelector('Album')?.textContent || undefined,
            genre: node.querySelector('Genre')?.textContent || undefined,
            year: node.querySelector('Year')?.textContent || undefined,
            bpm: parseFloat(node.querySelector('Bpm')?.getAttribute('Bpm') || '0'),
            key: vdjKey ? (VDJ_KEY_MAP[vdjKey] || vdjKey) : undefined,
            rating: parseInt(node.querySelector('Infos')?.getAttribute('Rating') || '0', 10),
            playCount: parseInt(node.querySelector('Infos')?.getAttribute('Playcount') || '0', 10),
            cues,
            loops: [],
        });
    });
    return tracks;
};

const encodeLocation = (path: string): string => 'file://localhost/' + encodeURIComponent(path).replace(/'/g, '%27');

export const buildRekordboxXml = (tracks: GenericTrack[], xmlDoc: XMLDocument): XMLDocument => {
    const collectionNode = xmlDoc.querySelector('COLLECTION');
    if (!collectionNode) throw new Error('Invalid Rekordbox XML structure.');
    collectionNode.innerHTML = '';
    tracks.forEach((track, index) => {
        const trackNode = xmlDoc.createElement('TRACK');
        trackNode.setAttribute('TrackID', String(index + 1));
        if (track.title) trackNode.setAttribute('Name', track.title);
        if (track.artist) trackNode.setAttribute('Artist', track.artist);
        if (track.album) trackNode.setAttribute('Album', track.album);
        if (track.genre) trackNode.setAttribute('Genre', track.genre);
        if (track.year) trackNode.setAttribute('Year', track.year);
        if (track.bpm) trackNode.setAttribute('AverageBpm', String(track.bpm));
        if (track.key && CAMELOT_TO_RB_KEY[track.key]) trackNode.setAttribute('Tonality', CAMELOT_TO_RB_KEY[track.key]);
        if (track.rating) trackNode.setAttribute('Rating', String(track.rating));
        if (track.playCount) trackNode.setAttribute('PlayCount', String(track.playCount));
        trackNode.setAttribute('Location', encodeLocation(track.location));
        track.cues.forEach(cue => {
            const markNode = xmlDoc.createElement('POSITION_MARK');
            markNode.setAttribute('Name', cue.name);
            markNode.setAttribute('Type', String(cue.type));
            markNode.setAttribute('Start', String(cue.timeMs / 1000));
            trackNode.appendChild(markNode);
        });
         track.loops.forEach(loop => {
            const markNode = xmlDoc.createElement('POSITION_MARK');
            markNode.setAttribute('Name', 'Loop');
            markNode.setAttribute('Type', '3');
            markNode.setAttribute('Start', String(loop.startMs / 1000));
            markNode.setAttribute('End', String(loop.endMs / 1000));
            trackNode.appendChild(markNode);
        });
        collectionNode.appendChild(trackNode);
    });
    collectionNode.setAttribute('Entries', String(tracks.length));
    return xmlDoc;
};

export const buildVirtualDjXml = (tracks: GenericTrack[], xmlDoc: XMLDocument): XMLDocument => {
    const dbNode = xmlDoc.querySelector('VirtualDJ_Database');
    if (!dbNode) throw new Error('Invalid VirtualDJ XML structure.');
    dbNode.innerHTML = '';
    tracks.forEach(track => {
        const songNode = xmlDoc.createElement('Song');
        songNode.setAttribute('FilePath', track.location);
        const addTextNode = (parent: Element, tagName: string, textContent: string | undefined) => { if (textContent) { const node = xmlDoc.createElement(tagName); node.textContent = textContent; parent.appendChild(node); } };
        addTextNode(songNode, 'Title', track.title);
        addTextNode(songNode, 'Artist', track.artist);
        addTextNode(songNode, 'Album', track.album);
        addTextNode(songNode, 'Genre', track.genre);
        addTextNode(songNode, 'Year', track.year);
        const infosNode = xmlDoc.createElement('Infos');
        if (track.rating) infosNode.setAttribute('Rating', String(track.rating));
        if (track.playCount) infosNode.setAttribute('Playcount', String(track.playCount));
        songNode.appendChild(infosNode);
        if (track.bpm) { const bpmNode = xmlDoc.createElement('Bpm'); bpmNode.setAttribute('Bpm', String(track.bpm)); songNode.appendChild(bpmNode); }
        if (track.key && CAMELOT_TO_VDJ_KEY[track.key]) addTextNode(songNode, 'Key', CAMELOT_TO_VDJ_KEY[track.key]);
        track.cues.forEach((cue, index) => {
            const poiNode = xmlDoc.createElement('Poi');
            poiNode.setAttribute('Pos', String(Math.round(cue.timeMs * 1000)));
            poiNode.setAttribute('Name', cue.name || `Cue ${index + 1}`);
            poiNode.setAttribute('Type', 'cue');
            songNode.appendChild(poiNode);
        });
        dbNode.appendChild(songNode);
    });
    return xmlDoc;
};

const audioFileToGenericTrack = (file: AudioFile, index: number): GenericTrack => {
    const tags = file.fetchedTags || file.originalTags;
    return {
        location: file.webkitRelativePath || file.file.name,
        title: tags.title,
        artist: tags.artist,
        album: tags.album,
        genre: tags.genre,
        year: tags.year,
        bpm: tags.bpm,
        key: tags.key,
        cues: file.hotcues.map(hc => ({ timeMs: hc.time * 1000, name: `Cue ${hc.num}`, type: 0 })),
        loops: [],
    };
};

export const exportPlaylistToRekordboxXml = (playlistFiles: AudioFile[], playlistName: string): string => {
    const xmlString = `<?xml version="1.0" encoding="UTF-8"?>
<DJ_PLAYLISTS Version="1.0.0">
    <PRODUCT Name="rekordbox" Version="6.5.3" Company="AlphaTheta, Inc."/>
    <COLLECTION Entries="${playlistFiles.length}"></COLLECTION>
    <PLAYLISTS>
        <NODE Type="0" Name="ROOT" Count="1">
            <NODE Type="1" Name="${playlistName}" KeyType="0" Entries="${playlistFiles.length}">
            </NODE>
        </NODE>
    </PLAYLISTS>
</DJ_PLAYLISTS>`;
    
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlString, "application/xml");

    const genericTracks = playlistFiles.map(audioFileToGenericTrack);
    buildRekordboxXml(genericTracks, xmlDoc);

    const playlistNode = xmlDoc.querySelector(`NODE[Name="${playlistName}"]`);
    if (playlistNode) {
        const trackIds = Array.from(xmlDoc.querySelectorAll('COLLECTION > TRACK')).map(t => t.getAttribute('TrackID'));
        trackIds.forEach((id, index) => {
            const trackNode = xmlDoc.createElement('TRACK');
            trackNode.setAttribute('Key', id!);
            playlistNode.appendChild(trackNode);
        });
    }

    const serializer = new XMLSerializer();
    return serializer.serializeToString(xmlDoc);
};

export const exportPlaylistToVirtualDjXml = (playlistFiles: AudioFile[], playlistName: string): string => {
     const xmlString = `<?xml version="1.0" encoding="UTF-8"?>
<VirtualDJ_Database Version="8.5">
</VirtualDJ_Database>`;
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlString, "application/xml");

    const genericTracks = playlistFiles.map(audioFileToGenericTrack);
    buildVirtualDjXml(genericTracks, xmlDoc);
    
    // In VDJ, playlists are separate files, so we can't embed them here.
    // This function will export the DB part. A separate M3U would be needed for the playlist itself.
    // For simplicity, we just export the collection for now.
    
    const serializer = new XMLSerializer();
    return serializer.serializeToString(xmlDoc);
}