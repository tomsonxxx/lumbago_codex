// Lumbago — Library Browser (real data, no mocks)
const { useState, useMemo, useRef } = React;

const COLS = [
  { key:'title',     label:'Tytuł',    w:'24%' },
  { key:'artist',    label:'Artysta',  w:'16%' },
  { key:'album',     label:'Album',    w:'14%' },
  { key:'genre',     label:'Gatunek',  w:'10%' },
  { key:'bpm',       label:'BPM',      w:'6%'  },
  { key:'key',       label:'Ton.',     w:'6%'  },
  { key:'duration',  label:'Czas',     w:'7%'  },
  { key:'format',    label:'Format',   w:'6%'  },
  { key:'analyzed',  label:'AI',       w:'8%'  },
];

function CoverArt({ track, size = 40 }) {
  const hues = [240,270,200,320,180,290,160,210,300,190,250,340];
  const idx = track ? (track.title.charCodeAt(0) + (track.artist.charCodeAt(0)||0)) % hues.length : 0;
  const h = hues[idx];
  if (track?.coverUrl) {
    return <img src={track.coverUrl} style={{width:size,height:size,borderRadius:4,objectFit:'cover',flexShrink:0}} alt="" />;
  }
  return (
    <div style={{width:size,height:size,borderRadius:4,flexShrink:0,background:`linear-gradient(135deg,hsl(${h},60%,18%),hsl(${h+40},65%,32%))`,display:'flex',alignItems:'center',justifyContent:'center',fontSize:size*0.4,color:'rgba(255,255,255,0.5)'}}>
      ♪
    </div>
  );
}

function TrackRow({ track, selected, onSelect, onDblClick }) {
  return (
    <div className={`lmb-track-row ${selected?'lmb-track-row--selected':''}`} onClick={()=>onSelect(track)} onDoubleClick={()=>onDblClick(track)}>
      <div className="lmb-track-cell" style={{width:COLS[0].w,display:'flex',alignItems:'center',gap:9}}>
        <CoverArt track={track} size={30} />
        <div style={{overflow:'hidden'}}>
          <div className="lmb-track-title">{track.title}</div>
        </div>
      </div>
      <div className="lmb-track-cell" style={{width:COLS[1].w}}><span className="lmb-track-sub">{track.artist||'—'}</span></div>
      <div className="lmb-track-cell" style={{width:COLS[2].w}}><span className="lmb-track-sub">{track.album||'—'}</span></div>
      <div className="lmb-track-cell" style={{width:COLS[3].w}}>{track.genre ? <Badge>{track.genre}</Badge> : <span className="lmb-track-sub">—</span>}</div>
      <div className="lmb-track-cell" style={{width:COLS[4].w}}>{track.bpm ? <span className="lmb-bpm">{track.bpm}</span> : <span className="lmb-track-sub">—</span>}</div>
      <div className="lmb-track-cell" style={{width:COLS[5].w}}>{track.key ? <KeyBadge k={track.key}/> : <span className="lmb-track-sub">—</span>}</div>
      <div className="lmb-track-cell" style={{width:COLS[6].w}}><span className="lmb-track-sub">{track.duration}</span></div>
      <div className="lmb-track-cell" style={{width:COLS[7].w}}><span className="lmb-format-badge">{track.format}</span></div>
      <div className="lmb-track-cell" style={{width:COLS[8].w}}>
        {track.analyzed
          ? <span style={{color:'#39ffb6',fontSize:11}}>✓ MB</span>
          : <span style={{color:'var(--text-muted)',fontSize:11}}>—</span>}
      </div>
    </div>
  );
}

function GridCard({ track, selected, onSelect, onDblClick }) {
  return (
    <div className={`lmb-grid-card ${selected?'lmb-grid-card--selected':''}`} onClick={()=>onSelect(track)} onDoubleClick={()=>onDblClick(track)}>
      <CoverArt track={track} size={90} />
      <div style={{marginTop:8}}>
        <div className="lmb-track-title" style={{fontSize:12,marginBottom:2}}>{track.title}</div>
        <div className="lmb-track-sub" style={{fontSize:11}}>{track.artist||'—'}</div>
        <div style={{display:'flex',gap:6,marginTop:6,flexWrap:'wrap',alignItems:'center'}}>
          {track.bpm && <span className="lmb-bpm">{track.bpm}</span>}
          {track.key && <KeyBadge k={track.key}/>}
          <span className="lmb-format-badge">{track.format}</span>
        </div>
        {track.analyzed && <div style={{marginTop:4}}><span style={{color:'#39ffb6',fontSize:10}}>✓ MusicBrainz</span></div>}
      </div>
    </div>
  );
}

function DetailPanel({ track, onPlay, onSearch }) {
  if (!track) return (
    <div className="lmb-detail-empty">
      <div style={{fontSize:48,marginBottom:12}}>♫</div>
      <div style={{color:'var(--text-muted)',textAlign:'center',lineHeight:1.6}}>Wybierz utwór<br/>aby zobaczyć szczegóły</div>
    </div>
  );
  const fields = [
    ['Artysta', track.artist||'—'],
    ['Album', track.album||'—'],
    ['Gatunek', track.genre||'—'],
    ['BPM', track.bpm||'—'],
    ['Tonacja', track.key ? <KeyBadge k={track.key}/> : '—'],
    ['Rok', track.year||'—'],
    ['Czas', track.duration],
    ['Format', track.format],
    ['Rozmiar', track.size],
  ];
  return (
    <div className="lmb-detail">
      <div className="lmb-detail-art">
        <CoverArt track={track} size={112} />
        <div style={{flex:1,minWidth:0}}>
          <div style={{fontSize:14,fontWeight:700,marginBottom:4,lineHeight:1.3}}>{track.title}</div>
          <div style={{color:'var(--text-muted)',fontSize:12,marginBottom:4}}>{track.artist||'Nieznany artysta'}</div>
          <StarRating value={track.rating} />
          {track.analyzed && <div style={{marginTop:6}}><Badge color="#39ffb6">✓ MusicBrainz</Badge></div>}
        </div>
      </div>
      <WaveformPlaceholder progress={0} />
      <div className="lmb-detail-grid">
        {fields.map(([k,v]) => (
          <div key={k} className="lmb-detail-row">
            <span className="lmb-detail-label">{k}</span>
            <span className="lmb-detail-val">{v}</span>
          </div>
        ))}
      </div>
      {track.comment && <div style={{fontSize:11,color:'var(--text-muted)',marginTop:4,fontStyle:'italic'}}>"{track.comment}"</div>}
      {track.trackTags?.length > 0 && (
        <div style={{display:'flex',gap:4,flexWrap:'wrap',marginTop:8}}>
          {track.trackTags.map(t=><Badge key={t}>#{t}</Badge>)}
        </div>
      )}
      <div style={{marginTop:8,fontSize:10,color:'var(--border-accent)',wordBreak:'break-all',lineHeight:1.5}}>{track.path}</div>
      <div style={{display:'flex',gap:8,marginTop:12,flexWrap:'wrap'}}>
        <Btn variant="primary" onClick={()=>onPlay(track)} style={{flex:1}}>▶ Odtwórz</Btn>
        <Btn onClick={()=>onSearch(track)} title="Wyszukaj metadane online">🔍 Online</Btn>
      </div>
    </div>
  );
}

function EmptyLibrary({ onImport }) {
  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',height:'100%',gap:20,padding:40}}>
      <div style={{fontSize:72,opacity:0.3}}>♫</div>
      <div style={{fontSize:20,fontWeight:700,color:'var(--text)'}}>Biblioteka jest pusta</div>
      <div style={{fontSize:13,color:'var(--text-muted)',textAlign:'center',maxWidth:340,lineHeight:1.7}}>
        Kliknij przycisk poniżej, aby wybrać folder z plikami audio.<br/>
        Obsługiwane formaty: MP3, FLAC, WAV, M4A, AIFF, OGG, AAC
      </div>
      <Btn variant="primary" onClick={onImport} style={{fontSize:15,padding:'12px 28px'}}>⊕ Wybierz folder z muzyką</Btn>
    </div>
  );
}

function LibraryView({ tracks, onPlay, onOpenTagger, onOpenImport, onSearchTrack }) {
  const [view, setView] = useState('list');
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState('');
  const [filterGenre, setFilterGenre] = useState('');
  const [sortKey, setSortKey] = useState('title');
  const [sortDir, setSortDir] = useState(1);

  // Derive genre list from actual tracks
  const genres = useMemo(() => {
    const set = new Set(tracks.map(t=>t.genre).filter(Boolean));
    return ['', ...Array.from(set).sort()];
  }, [tracks]);

  const filtered = useMemo(() => tracks.filter(t => {
    const q = search.toLowerCase();
    const matchQ = !q || t.title.toLowerCase().includes(q) || (t.artist||'').toLowerCase().includes(q) || (t.album||'').toLowerCase().includes(q) || t.path.toLowerCase().includes(q);
    const matchG = !filterGenre || t.genre === filterGenre;
    return matchQ && matchG;
  }).sort((a,b) => {
    const va = a[sortKey]||'', vb = b[sortKey]||'';
    if (typeof va === 'string') return va.localeCompare(vb,'pl') * sortDir;
    return (Number(va) - Number(vb)) * sortDir;
  }), [tracks, search, filterGenre, sortKey, sortDir]);

  const handleSort = key => { if (sortKey===key) setSortDir(d=>-d); else { setSortKey(key); setSortDir(1); } };

  const notAnalyzed = tracks.filter(t=>!t.analyzed).length;

  if (tracks.length === 0) return <EmptyLibrary onImport={onOpenImport} />;

  return (
    <div className="lmb-library">
      <div className="lmb-toolbar">
        <div className="lmb-search-wrap">
          <span className="lmb-search-icon">⌕</span>
          <input className="lmb-search" placeholder="Szukaj tytułu, artysty, albumu, ścieżki…" value={search} onChange={e=>setSearch(e.target.value)} />
          {search && <button className="lmb-search-clear" onClick={()=>setSearch('')}>✕</button>}
        </div>
        <select className="lmb-select" value={filterGenre} onChange={e=>setFilterGenre(e.target.value)}>
          <option value="">Wszystkie gatunki</option>
          {genres.filter(Boolean).map(g=><option key={g} value={g}>{g}</option>)}
        </select>
        <div className="lmb-view-toggle">
          <button className={`lmb-view-btn ${view==='list'?'active':''}`} onClick={()=>setView('list')} title="Lista">☰</button>
          <button className={`lmb-view-btn ${view==='grid'?'active':''}`} onClick={()=>setView('grid')} title="Siatka">⊞</button>
        </div>
        <Btn variant="primary" onClick={onOpenImport}>⊕ Dodaj muzykę</Btn>
        {notAnalyzed > 0 && <Btn variant="accent2" onClick={onOpenTagger}>✦ Wzbogać metadane ({notAnalyzed})</Btn>}
      </div>

      <div className="lmb-stats-bar">
        <span>{filtered.length}{filtered.length!==tracks.length?` / ${tracks.length}`:''} utworów</span>
        <span>·</span>
        <span style={{color:'#39ffb6'}}>{tracks.filter(t=>t.analyzed).length} z metadanymi online</span>
        {notAnalyzed > 0 && <><span>·</span><span style={{color:'var(--accent2)'}}>{notAnalyzed} bez analizy</span></>}
      </div>

      <div className="lmb-library-body">
        <div className="lmb-library-main">
          {view === 'list' ? (
            <div className="lmb-track-list">
              <div className="lmb-track-header">
                {COLS.map(c=>(
                  <div key={c.key} className="lmb-track-cell lmb-track-header-cell" style={{width:c.w}} onClick={()=>handleSort(c.key)}>
                    {c.label}{sortKey===c.key?(sortDir===1?' ↑':' ↓'):''}
                  </div>
                ))}
              </div>
              <div className="lmb-track-rows">
                {filtered.length === 0
                  ? <div style={{padding:40,textAlign:'center',color:'var(--text-muted)'}}>Brak wyników dla "{search}"</div>
                  : filtered.map(t=><TrackRow key={t.id} track={t} selected={selected?.id===t.id} onSelect={setSelected} onDblClick={onPlay}/>)}
              </div>
            </div>
          ) : (
            <div className="lmb-grid">
              {filtered.map(t=><GridCard key={t.id} track={t} selected={selected?.id===t.id} onSelect={setSelected} onDblClick={onPlay}/>)}
            </div>
          )}
        </div>
        <div className="lmb-detail-panel">
          <DetailPanel track={selected} onPlay={onPlay} onSearch={onSearchTrack} />
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { LibraryView, CoverArt });
