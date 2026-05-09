// Lumbago — Unified Metadata API
// Providers: MusicBrainz, Discogs, Last.fm, OpenAI-compatible AI (OpenAI/Grok/DeepSeek)
(function() {

  /* ── SETTINGS HELPERS ── */
  const SETTINGS_KEY = 'lmb_settings';

  function loadSettings() {
    try { return JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}'); }
    catch(e) { return {}; }
  }

  /* ── RATE LIMITER ── */
  function makeRateLimiter(intervalMs) {
    let last = 0;
    return async function() {
      const wait = Math.max(0, intervalMs - (Date.now() - last));
      if (wait > 0) await new Promise(r => setTimeout(r, wait));
      last = Date.now();
    };
  }
  const mbThrottle = makeRateLimiter(1100);
  const discogsThrottle = makeRateLimiter(1100);

  /* ── MUSICBRAINZ ── */
  const MB_BASE = 'https://musicbrainz.org/ws/2';
  const MB_UA   = 'LumbagoMusicAI/1.0 (contact@lumbago.app)';
  const MB_HDR  = { 'Accept': 'application/json', 'User-Agent': MB_UA };

  async function mbFetch(url) {
    await mbThrottle();
    const r = await fetch(url, { headers: MB_HDR });
    if (!r.ok) throw new Error(`MusicBrainz HTTP ${r.status}`);
    return r.json();
  }

  async function searchMusicBrainz(artist, title, filename) {
    const parts = [];
    if (title)  parts.push(`recording:"${title.replace(/"/g,'').slice(0,60)}"`);
    if (artist) parts.push(`artist:"${artist.replace(/"/g,'').slice(0,60)}"`);
    // fallback: filename
    if (!parts.length && filename) parts.push(`recording:"${filename.replace(/\.[^.]+$/,'').replace(/[-_]/g,' ').slice(0,60)}"`);
    if (!parts.length) return [];

    const q = encodeURIComponent(parts.join(' AND '));
    const data = await mbFetch(`${MB_BASE}/recording/?query=${q}&limit=5&fmt=json`);
    return (data.recordings || []).map(rec => {
      const rel = rec.releases?.[0];
      const artistStr = (rec['artist-credit'] || []).map(a => a.name || a.artist?.name || '').filter(Boolean).join(', ');
      return {
        source: 'MusicBrainz',
        mbid:   rec.id,
        score:  rec.score || 0,
        title:  rec.title || title,
        artist: artistStr || artist,
        album:  rel?.title || '',
        year:   (rel?.date || '').slice(0,4),
        genre:  '',
        tags:   [],
      };
    });
  }

  async function mbGetTags(mbid) {
    try {
      const d = await mbFetch(`${MB_BASE}/recording/${mbid}?inc=tags+genres&fmt=json`);
      return {
        tags:   (d.tags   || []).sort((a,b)=>b.count-a.count).slice(0,8).map(t=>t.name),
        genres: (d.genres || []).sort((a,b)=>b.count-a.count).slice(0,4).map(g=>g.name),
      };
    } catch(e) { return { tags:[], genres:[] }; }
  }

  /* ── DISCOGS ── */
  const DISCOGS_BASE = 'https://api.discogs.com';

  async function searchDiscogs(artist, title, token) {
    await discogsThrottle();
    const q = encodeURIComponent([artist, title].filter(Boolean).join(' '));
    const url = `${DISCOGS_BASE}/database/search?q=${q}&type=release${token ? `&token=${token}` : ''}`;
    const r = await fetch(url, { headers: { 'User-Agent': MB_UA, 'Accept': 'application/json' } });
    if (!r.ok) throw new Error(`Discogs HTTP ${r.status}`);
    const data = await r.json();
    return (data.results || []).slice(0,5).map(res => ({
      source:  'Discogs',
      id:      res.id,
      score:   res.community?.have ? Math.min(99, Math.round(res.community.have / 10)) : 50,
      title:   res.title?.split(' - ').slice(1).join(' - ') || title,
      artist:  res.title?.split(' - ')[0] || artist,
      album:   res.title || '',
      year:    res.year ? String(res.year) : '',
      genre:   res.genre?.[0] || '',
      style:   res.style?.[0] || '',
      label:   res.label?.[0] || '',
      country: res.country || '',
      tags:    [...(res.genre||[]), ...(res.style||[])].slice(0,8),
      thumb:   res.thumb || '',
    }));
  }

  /* ── LAST.FM ── */
  const LASTFM_BASE = 'https://ws.audioscrobbler.com/2.0';

  async function searchLastFm(artist, title, apiKey) {
    if (!apiKey) throw new Error('Brak klucza Last.fm API');
    const params = new URLSearchParams({
      method: 'track.getInfo',
      api_key: apiKey,
      artist: artist || '',
      track: title || '',
      autocorrect: '1',
      format: 'json',
    });
    const r = await fetch(`${LASTFM_BASE}/?${params}`);
    if (!r.ok) throw new Error(`Last.fm HTTP ${r.status}`);
    const data = await r.json();
    if (data.error) throw new Error(`Last.fm: ${data.message}`);
    const t = data.track;
    if (!t) return [];
    return [{
      source: 'Last.fm',
      score:  85,
      title:  t.name || title,
      artist: t.artist?.name || artist,
      album:  t.album?.title || '',
      year:   '',
      genre:  '',
      tags:   (t.toptags?.tag || []).slice(0,8).map(tag=>tag.name),
      playcount: t.playcount,
      listeners: t.listeners,
    }];
  }

  /* ── AI (OpenAI-compatible: OpenAI / Grok / DeepSeek) ── */
  const AI_CONFIGS = {
    openai:   { url: 'https://api.openai.com/v1',   model: 'gpt-4o-mini' },
    grok:     { url: 'https://api.x.ai/v1',         model: 'grok-3-mini' },
    deepseek: { url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  };

  function buildAIPrompt(track) {
    return `You are a music metadata expert and DJ tool. Given this audio file information, return accurate metadata as JSON.

File info:
- Filename: ${track.filename}
- Title (from tags): ${track.title || 'unknown'}
- Artist (from tags): ${track.artist || 'unknown'}
- Album (from tags): ${track.album || 'unknown'}
- Current genre: ${track.genre || 'unknown'}
- BPM: ${track.bpm || 'unknown'}
- Format: ${track.format}

Return ONLY a valid JSON object (no markdown, no explanation) with these fields:
{
  "title": "corrected title",
  "artist": "corrected artist name",
  "album": "album name or empty string",
  "year": "release year as string or empty",
  "genre": "specific music genre",
  "mood": "mood descriptor (e.g. Energetyczny, Spokojny, Taneczny, Mroczny, Marzycielski)",
  "bpm_estimate": 128,
  "key": "Camelot key notation e.g. 8A or empty",
  "energy": 0.8,
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "confidence": 0.85
}`;
  }

  async function enrichWithAI(track, settings) {
    const provider = settings.aiProvider || 'openai';
    const cfg = AI_CONFIGS[provider];
    if (!cfg) throw new Error(`Nieznany dostawca AI: ${provider}`);

    let apiKey = settings[`${provider}Key`] || '';
    let baseUrl = provider === 'openai' ? (settings.openaiUrl || cfg.url) : cfg.url;
    let model   = provider === 'openai' ? (settings.openaiModel || cfg.model) : cfg.model;

    if (!apiKey) throw new Error(`Brak klucza API dla ${provider}. Ustaw go w Ustawieniach → API.`);

    const prompt = buildAIPrompt(track);
    const res = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.1,
        max_tokens: 400,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(()=>({}));
      throw new Error(`${provider} API błąd ${res.status}: ${err.error?.message || res.statusText}`);
    }

    const data = await res.json();
    const content = data.choices?.[0]?.message?.content || '{}';
    // Strip markdown code fences if present
    const clean = content.replace(/^```json?\s*/,'').replace(/\s*```$/,'').trim();
    const parsed = JSON.parse(clean);

    return {
      source:     provider.charAt(0).toUpperCase() + provider.slice(1) + ' AI',
      score:      Math.round((parsed.confidence || 0.7) * 100),
      title:      parsed.title  || track.title,
      artist:     parsed.artist || track.artist,
      album:      parsed.album  || track.album,
      year:       parsed.year   || track.year,
      genre:      parsed.genre  || track.genre,
      mood:       parsed.mood   || '',
      bpm:        parsed.bpm_estimate ? String(parsed.bpm_estimate) : track.bpm,
      key:        parsed.key    || track.key,
      energy:     parsed.energy || null,
      tags:       parsed.tags   || [],
    };
  }

  /* ── UNIFIED ENRICHMENT PIPELINE ── */
  async function enrichTrack(track, onStatus) {
    const settings = loadSettings();
    const result = { suggestions: [], bestMatch: null, tags: [], error: null };

    const providers = settings.searchProviders || ['musicbrainz'];

    for (const provider of providers) {
      try {
        if (provider === 'musicbrainz') {
          onStatus && onStatus('Szukam w MusicBrainz…');
          const recs = await searchMusicBrainz(track.artist, track.title, track.filename);
          result.suggestions.push(...recs);
          if (recs[0]?.score >= 75 && recs[0].mbid) {
            onStatus && onStatus('Pobieram tagi MB…');
            const extra = await mbGetTags(recs[0].mbid);
            recs[0].tags  = extra.tags;
            recs[0].genre = extra.genres[0] || recs[0].genre;
          }
        }

        if (provider === 'discogs') {
          onStatus && onStatus('Szukam w Discogs…');
          const recs = await searchDiscogs(track.artist, track.title, settings.discogsToken);
          result.suggestions.push(...recs);
        }

        if (provider === 'lastfm') {
          onStatus && onStatus('Szukam w Last.fm…');
          const recs = await searchLastFm(track.artist, track.title, settings.lastfmKey);
          result.suggestions.push(...recs);
        }

        if (provider === 'ai') {
          onStatus && onStatus(`Pytam ${settings.aiProvider || 'AI'}…`);
          const aiResult = await enrichWithAI(track, settings);
          result.suggestions.push(aiResult);
        }
      } catch(e) {
        result.suggestions.push({ source: provider, error: e.message, score: 0 });
      }
    }

    // Pick best match (highest score, no error)
    const valid = result.suggestions.filter(s => !s.error && s.score > 0);
    valid.sort((a,b) => b.score - a.score);
    result.bestMatch = valid[0] || null;
    result.tags = result.bestMatch?.tags || [];

    return result;
  }

  window.MetaApi = {
    searchMusicBrainz,
    searchDiscogs,
    searchLastFm,
    enrichWithAI,
    enrichTrack,
    loadSettings,
    SETTINGS_KEY,
  };
})();
