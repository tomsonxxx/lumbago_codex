// Lumbago — File System (instant import, lazy tag enrichment)
(function() {
  const AUDIO_EXTS = new Set(['mp3','flac','wav','m4a','aiff','aif','ogg','opus','aac','wma']);

  function formatDuration(sec) {
    if (!sec || isNaN(sec) || !isFinite(sec) || sec <= 0) return '—';
    return `${Math.floor(sec/60)}:${String(Math.floor(sec%60)).padStart(2,'0')}`;
  }

  // Phase 1: INSTANT scan — just filter audio files, no async ops
  function quickScan(files) {
    const audioFiles = Array.from(files).filter(f => {
      const ext = (f.name.split('.').pop() || '').toLowerCase();
      return AUDIO_EXTS.has(ext);
    });

    return audioFiles.map((file, i) => {
      const ext = (file.name.split('.').pop() || '').toUpperCase();
      const rawPath = file.webkitRelativePath || file.name;
      // Guess title/artist from filename (Artist - Title pattern)
      const base = file.name.replace(/\.[^.]+$/, '');
      const parts = base.split(/\s*[-–]\s*/);
      const title = parts.length >= 2 ? parts.slice(1).join(' - ').trim() : base;
      const artist = parts.length >= 2 ? parts[0].trim() : '';

      return {
        id: `${Date.now()}_${i}_${Math.random().toString(36).slice(2,6)}`,
        file,
        blobUrl: null,
        path: rawPath,
        filename: file.name,
        title,
        artist,
        album: '',
        genre: '',
        year: '',
        bpm: '',
        key: '',
        duration: '—',
        durationSec: 0,
        mood: '',
        trackTags: [],
        rating: 0,
        sizeBytes: file.size,
        size: file.size > 1048576
          ? (file.size / 1048576).toFixed(1) + ' MB'
          : (file.size / 1024).toFixed(0) + ' KB',
        format: ext,
        analyzed: false,
        mbResult: null,
        coverUrl: null,
        comment: '',
        dateAdded: new Date().toLocaleDateString('pl-PL'),
        tagsLoaded: false,
      };
    });
  }

  // Phase 2: Background tag enrichment — call after tracks are in state
  // Processes one track at a time, calls onUpdate(trackId, patch) for each
  function enrichTagsBackground(tracks, onUpdate, onDone) {
    let cancelled = false;
    let i = 0;

    async function processNext() {
      if (cancelled || i >= tracks.length) {
        if (onDone) onDone();
        return;
      }
      const track = tracks[i++];
      if (track.tagsLoaded || !track.file) {
        setTimeout(processNext, 0);
        return;
      }

      const patch = { tagsLoaded: true };

      // Read tags
      if (typeof jsmediatags !== 'undefined') {
        try {
          const tags = await new Promise((res) => {
            let done = false;
            const timer = setTimeout(() => { if (!done) { done = true; res({}); } }, 2500);
            jsmediatags.read(track.file, {
              onSuccess: r => { if (!done) { done = true; clearTimeout(timer); res(r.tags || {}); } },
              onError:   () => { if (!done) { done = true; clearTimeout(timer); res({}); } },
            });
          });

          if (tags.title)  patch.title  = tags.title;
          if (tags.artist) patch.artist = tags.artist;
          if (tags.album)  patch.album  = tags.album;
          if (tags.year)   patch.year   = tags.year;
          if (tags.genre)  patch.genre  = tags.genre.replace(/^\(\d+\)/, '').trim();
          if (tags.bpm)    patch.bpm    = String(tags.bpm).split('\0')[0].trim();
          if (tags.initialKey) patch.key = tags.initialKey;
          if (tags.comment) patch.comment = typeof tags.comment === 'object' ? (tags.comment.text || '') : tags.comment;

          // Cover art
          if (tags.picture && tags.picture.data) {
            try {
              const { data, format } = tags.picture;
              const blob = new Blob([new Uint8Array(data)], { type: format || 'image/jpeg' });
              patch.coverUrl = URL.createObjectURL(blob);
            } catch(e) {}
          }

          // Duration from TLEN tag
          if (tags.TLEN) {
            const ms = parseInt(tags.TLEN, 10);
            if (!isNaN(ms) && ms > 0) {
              patch.durationSec = ms / 1000;
              patch.duration = formatDuration(patch.durationSec);
            }
          }
        } catch(e) {}
      }

      // Duration fallback via audio element (only if still missing and file < 30MB)
      if (!patch.durationSec && track.file.size < 30 * 1024 * 1024) {
        try {
          const dur = await new Promise(res => {
            const audio = document.createElement('audio');
            const url = URL.createObjectURL(track.file);
            let done = false;
            const timer = setTimeout(() => { if (!done) { done = true; URL.revokeObjectURL(url); res(0); } }, 1500);
            audio.addEventListener('loadedmetadata', () => {
              if (!done) { done = true; clearTimeout(timer); URL.revokeObjectURL(url); res(isFinite(audio.duration) ? audio.duration : 0); }
            }, { once: true });
            audio.addEventListener('error', () => { if (!done) { done = true; clearTimeout(timer); URL.revokeObjectURL(url); res(0); } }, { once: true });
            audio.preload = 'metadata'; audio.src = url;
          });
          if (dur > 0) { patch.durationSec = dur; patch.duration = formatDuration(dur); }
        } catch(e) {}
      }

      onUpdate(track.id, patch);
      // Small delay between files to keep UI responsive
      setTimeout(processNext, 20);
    }

    setTimeout(processNext, 100);
    return { cancel: () => { cancelled = true; } };
  }

  window.FileSystem = { quickScan, enrichTagsBackground, formatDuration, AUDIO_EXTS };
})();
