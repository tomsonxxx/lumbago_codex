// Lumbago — Internet Metadata APIs
(function() {
  const MB_BASE = 'https://musicbrainz.org/ws/2';
  const MB_UA = 'LumbagoMusicAI/1.0 (contact@lumbago.app)';
  const MB_HEADERS = { 'Accept': 'application/json', 'User-Agent': MB_UA };

  // Rate limiter: max 1 req/sec for MusicBrainz
  let lastMBCall = 0;
  async function mbFetch(url) {
    const now = Date.now();
    const wait = Math.max(0, 1100 - (now - lastMBCall));
    if (wait > 0) await new Promise(r => setTimeout(r, wait));
    lastMBCall = Date.now();
    const res = await fetch(url, { headers: MB_HEADERS });
    if (!res.ok) throw new Error(`MusicBrainz HTTP ${res.status}`);
    return res.json();
  }

  // Search recordings by artist + title
  async function searchRecording(artist, title) {
    const parts = [];
    if (title)  parts.push(`recording:"${title.replace(/"/g,'').slice(0,60)}"`);
    if (artist) parts.push(`artist:"${artist.replace(/"/g,'').slice(0,60)}"`);
    if (!parts.length) return [];
    const q = encodeURIComponent(parts.join(' AND '));
    const data = await mbFetch(`${MB_BASE}/recording/?query=${q}&limit=5&fmt=json`);
    return (data.recordings || []).map(rec => {
      const release = rec.releases?.[0];
      const artistCredit = (rec['artist-credit'] || []).map(a => a.name || a.artist?.name || '').filter(Boolean).join(', ');
      return {
        mbid: rec.id,
        score: rec.score || 0,
        title: rec.title || title,
        artist: artistCredit || artist,
        album: release?.title || '',
        year: (release?.date || '').slice(0, 4),
        genre: '',
        duration: rec.length ? FileSystem.formatDuration(rec.length / 1000) : '',
        source: 'MusicBrainz',
      };
    });
  }

  // Search by filename only (fallback)
  async function searchByFilename(filename) {
    const clean = filename.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' ');
    const q = encodeURIComponent(`recording:"${clean.slice(0,80)}"`);
    const data = await mbFetch(`${MB_BASE}/recording/?query=${q}&limit=3&fmt=json`);
    return (data.recordings || []).map(rec => {
      const release = rec.releases?.[0];
      const artistCredit = (rec['artist-credit'] || []).map(a => a.name || a.artist?.name || '').filter(Boolean).join(', ');
      return {
        mbid: rec.id,
        score: rec.score || 0,
        title: rec.title,
        artist: artistCredit,
        album: release?.title || '',
        year: (release?.date || '').slice(0, 4),
        source: 'MusicBrainz',
      };
    });
  }

  // Get tags/genres for a recording by MBID
  async function getRecordingTags(mbid) {
    try {
      const data = await mbFetch(`${MB_BASE}/recording/${mbid}?inc=tags+genres&fmt=json`);
      const tags = (data.tags || []).sort((a,b) => b.count - a.count).slice(0,8).map(t => t.name);
      const genres = (data.genres || []).sort((a,b) => b.count - a.count).slice(0,4).map(g => g.name);
      return { tags, genres };
    } catch(e) { return { tags: [], genres: [] }; }
  }

  // Cover Art Archive
  async function getCoverArt(releaseMbid) {
    try {
      const res = await fetch(`https://coverartarchive.org/release/${releaseMbid}/front-250`, {
        headers: { 'User-Agent': MB_UA }
      });
      if (res.ok) return res.url; // redirected to actual image
      return null;
    } catch(e) { return null; }
  }

  // Full enrichment pipeline for one track
  async function enrichTrack(track, onStatus) {
    const result = { original: track, suggestions: [], bestMatch: null, tags: [], genres: [] };
    try {
      onStatus && onStatus('Szukam w MusicBrainz…');
      let recs = [];
      if (track.artist || track.title) {
        recs = await searchRecording(track.artist, track.title);
      }
      if (!recs.length) {
        onStatus && onStatus('Próbuję po nazwie pliku…');
        recs = await searchByFilename(track.filename);
      }
      result.suggestions = recs;
      if (recs.length > 0) {
        const best = recs[0];
        result.bestMatch = best;
        if (best.score >= 80 && best.mbid) {
          onStatus && onStatus('Pobieram tagi i gatunki…');
          const extra = await getRecordingTags(best.mbid);
          result.tags = extra.tags;
          result.genres = extra.genres;
          result.bestMatch = { ...best, genre: extra.genres[0] || best.genre };
        }
      }
    } catch(e) {
      result.error = e.message;
    }
    return result;
  }

  window.MBApi = { searchRecording, searchByFilename, getRecordingTags, getCoverArt, enrichTrack };
})();
