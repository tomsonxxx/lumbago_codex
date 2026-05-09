// Lumbago — Root App (real data, no mocks)
const { useState, useCallback, useEffect } = React;

const NAV_ITEMS = [
  { id:'library',    icon:'♫', label:'Biblioteka' },
  { id:'playlists',  icon:'≡', label:'Playlisty' },
  { id:'duplicates', icon:'⊕', label:'Duplikaty' },
  { id:'renamer',    icon:'✎', label:'Renamer' },
  { id:'xml',        icon:'↔', label:'XML Konwerter' },
];

function Sidebar({ nav, setNav, onOpenImport, onOpenTagger, onOpenSettings, trackCount, notAnalyzed }) {
  return (
    <div className="lmb-sidebar">
      <div className="lmb-logo">
        <span className="lmb-logo-text">Lumbago</span>
        <span className="lmb-logo-sub">Music AI</span>
      </div>

      <button className="lmb-cta-import" onClick={onOpenImport}>
        <span className="lmb-cta-icon">⊕</span>
        <div>
          <div style={{fontWeight:700,fontSize:13}}>Importuj muzykę</div>
          <div style={{fontSize:11,opacity:0.75}}>Wybierz folder</div>
        </div>
      </button>

      <nav className="lmb-nav">
        {NAV_ITEMS.map(item => (
          <button key={item.id} className={`lmb-nav-item ${nav===item.id?'active':''}`} onClick={()=>setNav(item.id)}>
            <span className="lmb-nav-icon">{item.icon}</span>
            <span>{item.label}</span>
            {item.id==='library' && trackCount>0 && <span className="lmb-nav-count">{trackCount}</span>}
          </button>
        ))}
      </nav>

      <div className="lmb-sidebar-section">
        <div className="lmb-sidebar-section-title">Narzędzia online</div>
        <button className="lmb-tool-btn" onClick={onOpenTagger} title="Wyszukaj metadane w MusicBrainz">
          <span>🔍</span> MusicBrainz
          {notAnalyzed > 0 && <span className="lmb-tool-count">{notAnalyzed}</span>}
        </button>
      </div>

      <div className="lmb-sidebar-bottom">
        <button className="lmb-nav-item" onClick={onOpenSettings}>
          <span className="lmb-nav-icon">⚙</span>
          <span>Ustawienia</span>
        </button>
        <div className="lmb-version-pill">v1.0 · Cyber</div>
      </div>
    </div>
  );
}

function PlaceholderView({ icon, title, desc }) {
  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',height:'100%',color:'var(--text-muted)',gap:14}}>
      <div style={{fontSize:60}}>{icon}</div>
      <div style={{fontSize:18,fontWeight:700,color:'var(--text)'}}>{title}</div>
      <div style={{fontSize:13,maxWidth:320,textAlign:'center',lineHeight:1.7}}>{desc}</div>
    </div>
  );
}

// Persist library to sessionStorage (tracks without File refs for reload)
function saveMeta(tracks) {
  try {
    const meta = tracks.map(({ file, blobUrl, coverUrl, ...rest }) => rest);
    sessionStorage.setItem('lmb_meta', JSON.stringify(meta));
  } catch(e) {}
}

function App() {
  const [nav, setNav] = useState('library');
  const [tracks, setTracks] = useState([]);
  const [nowPlaying, setNowPlaying] = useState(null);
  const [nowIdx, setNowIdx] = useState(0);
  const [dialog, setDialog] = useState(null);
  const [searchTarget, setSearchTarget] = useState(null);
  const [tweakOpen, setTweakOpen] = useState(false);

  // Tweaks protocol
  useEffect(() => {
    const handler = e => {
      if (e.data?.type==='__activate_edit_mode')   setTweakOpen(true);
      if (e.data?.type==='__deactivate_edit_mode') setTweakOpen(false);
    };
    window.addEventListener('message', handler);
    window.parent.postMessage({ type:'__edit_mode_available' }, '*');
    return () => window.removeEventListener('message', handler);
  }, []);

  const handleImported = useCallback((newTracks) => {
    setTracks(prev => {
      const existing = new Set(prev.map(t => t.path));
      const fresh = newTracks.filter(t => !existing.has(t.path));
      const merged = [...prev, ...fresh];
      saveMeta(merged);

      // Phase 2: enrich tags in background — updates each track as tags arrive
      if (fresh.length > 0) {
        window.FileSystem.enrichTagsBackground(
          fresh,
          (trackId, patch) => {
            setTracks(cur => cur.map(t => t.id === trackId ? { ...t, ...patch } : t));
          },
          () => {} // onDone
        );
      }

      return merged;
    });
    setDialog(null);
    setNav('library');
  }, []);

  const handlePlay = useCallback((track) => {
    const idx = tracks.findIndex(t => t.id === track.id);
    setNowIdx(idx >= 0 ? idx : 0);
    setNowPlaying(track);
  }, [tracks]);

  const handleNext = useCallback(() => {
    const ni = Math.min(nowIdx + 1, tracks.length - 1);
    if (tracks[ni]) { setNowIdx(ni); setNowPlaying(tracks[ni]); }
  }, [nowIdx, tracks]);

  const handlePrev = useCallback(() => {
    const ni = Math.max(nowIdx - 1, 0);
    if (tracks[ni]) { setNowIdx(ni); setNowPlaying(tracks[ni]); }
  }, [nowIdx, tracks]);

  const handleSearchTrack = useCallback((track) => {
    setSearchTarget(track);
    setDialog('metasearch');
  }, []);

  const handleApplyMeta = useCallback((track, match, tags) => {
    setTracks(prev => prev.map(t => t.id === track.id ? {
      ...t,
      title:   match.title  || t.title,
      artist:  match.artist || t.artist,
      album:   match.album  || t.album,
      year:    match.year   || t.year,
      genre:   match.genre  || t.genre,
      trackTags: tags || t.trackTags,
      analyzed: true,
      mbResult: match,
    } : t));
  }, []);

  const handleApplyAll = useCallback((updates) => {
    setTracks(prev => {
      const map = {};
      updates.forEach(u => { map[u.id] = u; });
      return prev.map(t => {
        const u = map[t.id];
        if (!u) return t;
        const m = u.match;
        return {
          ...t,
          title:  m.title  || t.title,
          artist: m.artist || t.artist,
          album:  m.album  || t.album,
          year:   m.year   || t.year,
          genre:  m.genre  || t.genre,
          trackTags: u.tags || t.trackTags,
          analyzed: true,
          mbResult: m,
        };
      });
    });
  }, []);

  const notAnalyzed = tracks.filter(t => !t.analyzed).length;

  return (
    <div className="lmb-app">
      <Sidebar
        nav={nav} setNav={setNav}
        onOpenImport={() => setDialog('import')}
        onOpenTagger={() => setDialog('tagger')}
        onOpenSettings={() => setDialog('settings')}
        trackCount={tracks.length}
        notAnalyzed={notAnalyzed}
      />

      <div className="lmb-main">
        <div className="lmb-content">
          {nav==='library' && (
            <LibraryView
              tracks={tracks}
              onPlay={handlePlay}
              onOpenTagger={() => setDialog('tagger')}
              onOpenImport={() => setDialog('import')}
              onSearchTrack={handleSearchTrack}
            />
          )}
          {nav==='playlists'  && <PlaceholderView icon="≡" title="Playlisty" desc="Tworzenie i zarządzanie playlistami — wkrótce" />}
          {nav==='duplicates' && <PlaceholderView icon="⊕" title="Duplikaty" desc="Wykrywanie duplikatów po hash, fingerprint i tagach" />}
          {nav==='renamer'    && <PlaceholderView icon="✎" title="Renamer" desc="Masowe zmiany nazw według konfigurowalnych wzorców" />}
          {nav==='xml'        && <PlaceholderView icon="↔" title="XML Konwerter" desc="Import/eksport Rekordbox · VirtualDJ" />}
        </div>

        <PlayerBar track={nowPlaying} onNext={handleNext} onPrev={handlePrev} />
      </div>

      {/* Dialogs */}
      {dialog==='import'     && <ImportWizard onClose={()=>setDialog(null)} onImported={handleImported} />}
      {dialog==='tagger'     && <AiTaggerDialog tracks={tracks} onClose={()=>setDialog(null)} onApplyAll={handleApplyAll} />}
      {dialog==='metasearch' && searchTarget && <MetaSearchDialog track={searchTarget} onClose={()=>setDialog(null)} onApply={handleApplyMeta} />}
      {dialog==='settings'   && <SettingsDialog onClose={()=>setDialog(null)} />}

      {/* Tweaks panel */}
      {tweakOpen && (
        <div className="lmb-tweaks">
          <div className="lmb-tweaks-title">Tweaks</div>
          <div className="lmb-tweaks-row">
            <span>Otwórz dialog</span>
            <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
              {[['import','Import'],['tagger','MB Tagger'],['settings','Ustawienia']].map(([id,label])=>(
                <button key={id} className="lmb-tweak-btn" onClick={()=>setDialog(id)}>{label}</button>
              ))}
            </div>
          </div>
          <div className="lmb-tweaks-row">
            <span>Widok</span>
            <div style={{display:'flex',gap:6}}>
              {NAV_ITEMS.map(n=>(
                <button key={n.id} className={`lmb-tweak-btn ${nav===n.id?'active':''}`} onClick={()=>setNav(n.id)}>{n.label}</button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
