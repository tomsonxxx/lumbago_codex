// Lumbago — Dialogs (real file import + real MB search)
const { useState, useEffect, useRef, useCallback } = React;

/* ─── IMPORT WIZARD ─── */
function ImportWizard({ onClose, onImported }) {
  const [step, setStep] = useState(0); // 0=pick, 2=preview, 3=done
  const [foundTracks, setFoundTracks] = useState([]);
  const [error, setError] = useState('');
  const fileInputRef = useRef();

  const handleFiles = useCallback((files) => {
    setError('');
    try {
      if (!window.FileSystem || !window.FileSystem.quickScan) {
        setError('Błąd: moduł FileSystem nie załadował się. Odśwież stronę (Ctrl+F5).');
        return;
      }
      const tracks = window.FileSystem.quickScan(files);
      if (tracks.length === 0) {
        setError('Nie znaleziono plików audio w wybranym folderze. Obsługiwane: MP3, FLAC, WAV, M4A, AIFF, OGG, AAC.');
        return;
      }
      setFoundTracks(tracks);
      setStep(2);
    } catch(e) {
      setError('Błąd podczas skanowania: ' + e.message);
    }
  }, []);

  const confirmImport = () => {
    onImported(foundTracks);
    setStep(3);
  };

  return (
    <Modal title="Import muzyki" onClose={onClose} width={640}>
      {/* Step 0 — file picker */}
      {step === 0 && (
        <div className="lmb-wizard-body">
          <div className="lmb-wizard-icon">📁</div>
          <h3 style={{textAlign:'center',marginBottom:8}}>Wybierz folder z muzyką</h3>
          <p style={{color:'var(--text-muted)',textAlign:'center',marginBottom:24,lineHeight:1.6}}>
            Kliknij poniżej i wybierz folder. Wszystkie pliki audio<br/>zostaną zeskanowane rekurencyjnie.
          </p>
          <div style={{display:'flex',justifyContent:'center'}}>
            <label className="lmb-drop-zone" onClick={()=>fileInputRef.current?.click()}>
              <div style={{fontSize:40,marginBottom:12}}>⊕</div>
              <div style={{fontWeight:700,marginBottom:6}}>Kliknij, aby wybrać folder</div>
              <div style={{fontSize:12,color:'var(--text-muted)'}}>MP3 · FLAC · WAV · M4A · AIFF · OGG · AAC</div>
              <input
                ref={fileInputRef}
                type="file"
                accept="audio/*"
                multiple
                // @ts-ignore
                webkitdirectory=""
                directory=""
                style={{display:'none'}}
                onChange={e => e.target.files?.length && handleFiles(e.target.files)}
              />
            </label>
          </div>
          {error && <div style={{color:'var(--danger)',marginTop:16,textAlign:'center',fontSize:12}}>{error}</div>}
          <div style={{marginTop:20,fontSize:11,color:'var(--text-muted)',textAlign:'center',lineHeight:1.7}}>
            Możesz też wybrać wiele plików ręcznie zamiast całego folderu.
          </div>
        </div>
      )}



      {/* Step 2 — preview */}
      {step === 2 && (
        <div className="lmb-wizard-body">
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
            <div><strong style={{color:'var(--accent)'}}>{foundTracks.length}</strong> <span style={{color:'var(--text-muted)'}}>plików znalezionych</span></div>
            <div style={{fontSize:11,color:'var(--text-muted)'}}>
              {foundTracks.filter(t=>t.artist).length} z tagiem artysty · {foundTracks.filter(t=>t.album).length} z albumem
            </div>
          </div>
          <div className="lmb-import-list">
            {foundTracks.slice(0,50).map((t,i) => (
              <div key={i} className="lmb-import-row">
                <CoverArt track={t} size={28} />
                <div style={{flex:1,minWidth:0}}>
                  <div className="lmb-track-title" style={{fontSize:12}}>{t.title}</div>
                  <div className="lmb-track-sub" style={{fontSize:11}}>
                    {t.artist||'?'} · {t.duration} · {t.format} · {t.size}
                  </div>
                </div>
                {!t.artist && <span style={{fontSize:10,color:'var(--warn)',flexShrink:0}}>brak tagów</span>}
              </div>
            ))}
            {foundTracks.length > 50 && (
              <div style={{padding:'12px',textAlign:'center',color:'var(--text-muted)',fontSize:12}}>…i {foundTracks.length-50} więcej</div>
            )}
          </div>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginTop:16}}>
            <Btn onClick={()=>setStep(0)}>← Wróć</Btn>
            <Btn variant="primary" onClick={confirmImport} disabled={foundTracks.length===0}>
              ⊕ Dodaj {foundTracks.length} plików do biblioteki
            </Btn>
          </div>
        </div>
      )}

      {/* Step 3 — done */}
      {step === 3 && (
        <div className="lmb-wizard-body" style={{textAlign:'center'}}>
          <div style={{fontSize:56,marginBottom:12}}>🎵</div>
          <h3 style={{color:'var(--accent)',marginBottom:8}}>Gotowe!</h3>
          <p style={{color:'var(--text-muted)',marginBottom:20,lineHeight:1.7}}>
            Zaimportowano <strong style={{color:'var(--text)'}}>{foundTracks.length} plików</strong>.<br/>
            Możesz teraz wzbogacić metadane online za pomocą MusicBrainz.
          </p>
          <Btn variant="primary" onClick={onClose}>Przejdź do biblioteki →</Btn>
        </div>
      )}
    </Modal>
  );
}

/* ─── ONLINE METADATA SEARCH ─── */
function MetaSearchDialog({ track, onClose, onApply }) {
  const [status, setStatus] = useState('idle'); // idle, searching, done, error
  const [results, setResults] = useState([]);
  const [errMsg, setErrMsg] = useState('');
  const [selected, setSelected] = useState(null);
  const [tags, setTags] = useState([]);

  const search = async () => {
    setStatus('searching');
    setResults([]);
    setErrMsg('');
    setSelected(null);
    setTags([]);
    try {
      const enriched = await window.MetaApi.enrichTrack(track, setStatus);
      setResults(enriched.suggestions);
      setTags(enriched.tags);
      if (enriched.bestMatch) setSelected(enriched.bestMatch);
      setStatus('done');
    } catch(e) {
      setErrMsg(e.message);
      setStatus('error');
    }
  };

  useEffect(() => { search(); }, []);

  return (
    <Modal title="Wyszukiwanie metadanych online" onClose={onClose} width={640}>
      <div style={{marginBottom:12}}>
        <div style={{fontWeight:700,fontSize:14,marginBottom:2}}>{track.title}</div>
        <div style={{color:'var(--text-muted)',fontSize:12}}>{track.artist||'?'} · {track.path}</div>
      </div>

      {(status==='searching') && (
        <div style={{padding:'24px 0',textAlign:'center'}}>
          <span className="lmb-scan-anim" style={{fontSize:36}}>⟳</span>
          <div style={{color:'var(--text-muted)',marginTop:8,fontSize:13}}>{status === 'searching' ? 'Łączę z MusicBrainz…' : status}</div>
        </div>
      )}

      {status==='error' && (
        <div style={{color:'var(--danger)',padding:'16px 0',textAlign:'center'}}>
          <div style={{fontSize:24,marginBottom:8}}>⚠</div>
          <div>{errMsg}</div>
          <Btn style={{marginTop:12}} onClick={search}>Spróbuj ponownie</Btn>
        </div>
      )}

      {status==='done' && results.length === 0 && (
        <div style={{textAlign:'center',padding:'24px 0',color:'var(--text-muted)'}}>
          <div style={{fontSize:32,marginBottom:8}}>🔍</div>
          Nie znaleziono wyników w MusicBrainz.
          <div style={{marginTop:12}}><Btn onClick={search}>Spróbuj ponownie</Btn></div>
        </div>
      )}

      {results.length > 0 && (
        <>
          <div style={{fontSize:12,color:'var(--text-muted)',marginBottom:8}}>Wybierz najlepsze dopasowanie:</div>
          <div className="lmb-import-list" style={{maxHeight:280}}>
            {results.map((r,i) => (
              <div key={i} className={`lmb-import-row ${selected===r?'lmb-import-row--selected':''}`} onClick={()=>setSelected(r)} style={{cursor:'pointer'}}>
                <div style={{width:36,height:36,borderRadius:6,background:'var(--surface)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:18,flexShrink:0}}>♪</div>
                <div style={{flex:1,minWidth:0}}>
                  <div className="lmb-track-title" style={{fontSize:12}}>{r.title}</div>
                  <div className="lmb-track-sub" style={{fontSize:11}}>{r.artist} · {r.album||'—'} · {r.year||'—'}</div>
                </div>
                <div style={{fontSize:11,flexShrink:0}}>
                  <span style={{color: r.score>=80?'#39ffb6':r.score>=60?'var(--warn)':'var(--danger)',fontWeight:700}}>{r.score}%</span>
                </div>
              </div>
            ))}
          </div>
          {tags.length > 0 && (
            <div style={{marginTop:12,display:'flex',gap:6,flexWrap:'wrap'}}>
              <span style={{fontSize:11,color:'var(--text-muted)'}}>Tagi:</span>
              {tags.map(t=><Badge key={t}>#{t}</Badge>)}
            </div>
          )}
          <div style={{display:'flex',justifyContent:'flex-end',gap:8,marginTop:16,paddingTop:12,borderTop:'1px solid var(--border)'}}>
            <Btn onClick={onClose}>Anuluj</Btn>
            <Btn variant="primary" disabled={!selected} onClick={()=>{ onApply(track, selected, tags); onClose(); }}>
              ✓ Zastosuj metadane
            </Btn>
          </div>
        </>
      )}
    </Modal>
  );
}

/* ─── AI/MULTI-SOURCE BULK TAGGER ─── */
const PROVIDER_LABELS = {
  musicbrainz: { icon:'🎵', name:'MusicBrainz', free:true },
  discogs:     { icon:'💿', name:'Discogs',     free:true, needsKey:'discogsToken' },
  lastfm:      { icon:'📻', name:'Last.fm',     free:false, needsKey:'lastfmKey' },
  ai:          { icon:'✦',  name:'AI',          free:false, needsKey:'aiProvider' },
};

function ProviderChip({ id, active, onClick, settings }) {
  const p = PROVIDER_LABELS[id];
  const hasKey = !p.needsKey || !!settings[p.needsKey];
  return (
    <button
      className={`lmb-provider-btn ${active?'active':''} ${!hasKey?'disabled':''}`}
      onClick={onClick}
      title={!hasKey ? 'Brak klucza API — ustaw w Ustawieniach' : p.name}
    >
      {p.icon} {p.name} {p.free && <span style={{fontSize:9,opacity:0.6}}>bezpłatny</span>}
      {!hasKey && <span style={{fontSize:9,color:'var(--warn)'}}>⚠</span>}
    </button>
  );
}

function AiTaggerDialog({ tracks, onClose, onApplyAll }) {
  const settings = window.MetaApi?.loadSettings() || {};
  const [providers, setProviders] = useState(settings.searchProviders || ['musicbrainz']);
  const [running, setRunning] = useState(false);
  const [currentIdx, setCurrentIdx] = useState(-1);
  const [currentStatus, setCurrentStatus] = useState('');
  const [results, setResults] = useState({});
  const [accepted, setAccepted] = useState({});
  const [rejected, setRejected] = useState({});
  const [done, setDone] = useState(false);
  const abortRef = useRef(false);

  const toProcess = tracks.filter(t => !t.analyzed);

  const toggleProvider = id => {
    setProviders(prev => prev.includes(id) ? prev.filter(p=>p!==id) : [...prev, id]);
  };

  const runTagger = async () => {
    if (!providers.length) return;
    setRunning(true); setDone(false); setResults({}); setAccepted({}); setRejected({});
    abortRef.current = false;
    const list = toProcess.length > 0 ? toProcess : tracks.slice(0, 30);
    const settingsWithProviders = { ...settings, searchProviders: providers };

    for (let i = 0; i < list.length; i++) {
      if (abortRef.current) break;
      const track = list[i];
      setCurrentIdx(i);
      try {
        // temporarily override providers in settings
        const origSettings = window.MetaApi.loadSettings();
        localStorage.setItem(window.MetaApi.SETTINGS_KEY, JSON.stringify({...origSettings, searchProviders: providers}));
        const res = await window.MetaApi.enrichTrack(track, msg => setCurrentStatus(msg));
        localStorage.setItem(window.MetaApi.SETTINGS_KEY, JSON.stringify(origSettings));
        setResults(r => ({ ...r, [track.id]: res }));
        if (res.bestMatch && res.bestMatch.score >= 70) {
          setAccepted(a => ({ ...a, [track.id]: true }));
        }
      } catch(e) {
        setResults(r => ({ ...r, [track.id]: { error: e.message, suggestions:[], tags:[] } }));
      }
    }
    setCurrentIdx(-1); setRunning(false); setDone(true);
  };

  const resultEntries = tracks.filter(t => results[t.id]);
  const acceptAll = () => { const a={}; resultEntries.forEach(t=>{ if(results[t.id]?.bestMatch) a[t.id]=true; }); setAccepted(a); };
  const rejectAll  = () => { const r={}; resultEntries.forEach(t=>{ r[t.id]=true; }); setRejected(r); };

  const applyAccepted = () => {
    const updates = resultEntries
      .filter(t => accepted[t.id] && !rejected[t.id] && results[t.id]?.bestMatch)
      .map(t => ({ id: t.id, match: results[t.id].bestMatch, tags: results[t.id].tags }));
    onApplyAll(updates);
    onClose();
  };

  const progress = (currentIdx+1) / Math.max(toProcess.length || tracks.length, 1) * 100;

  return (
    <Modal title="Wzbogacanie metadanych" onClose={onClose} width={820}>
      {/* Provider selector */}
      <div style={{background:'var(--surface)',borderRadius:10,padding:'12px 14px',marginBottom:12}}>
        <div style={{fontSize:11,color:'var(--text-muted)',marginBottom:8,fontWeight:600,textTransform:'uppercase',letterSpacing:'0.5px'}}>Źródła wyszukiwania</div>
        <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
          {Object.keys(PROVIDER_LABELS).map(id => (
            <ProviderChip key={id} id={id} active={providers.includes(id)} onClick={()=>toggleProvider(id)} settings={settings} />
          ))}
        </div>
        {providers.includes('ai') && (
          <div style={{marginTop:8,fontSize:11,color:'var(--text-muted)'}}>
            AI: <strong style={{color:'var(--text)'}}>{settings.aiProvider || 'nie wybrano'}</strong>
            {!settings[`${settings.aiProvider}Key`] && <span style={{color:'var(--warn)'}}> — brak klucza API (Ustawienia → API)</span>}
          </div>
        )}
      </div>

      <div className="lmb-tagger-header">
        <div style={{fontSize:13}}>
          {toProcess.length > 0
            ? <span><strong style={{color:'var(--accent)'}}>{toProcess.length}</strong> <span style={{color:'var(--text-muted)'}}>do analizy</span></span>
            : <span style={{color:'var(--text-muted)'}}>{tracks.length} utworów · ponowna analiza</span>}
        </div>
        <div style={{display:'flex',gap:8}}>
          {running && <Btn variant="danger" onClick={()=>{abortRef.current=true}}>■ Stop</Btn>}
          {!running && <Btn variant="primary" onClick={runTagger} disabled={!providers.length}>🔍 Uruchom wyszukiwanie</Btn>}
        </div>
      </div>

      {(running || done) && (
        <div style={{marginBottom:12}}>
          <ProgressBar
            value={running ? Math.max(progress,2) : 100}
            label={running ? `${currentIdx+1}/${toProcess.length||tracks.length} — ${currentStatus}` : `Zakończono · ${resultEntries.length} wyników`}
            color={done?'#39ffb6':undefined}
          />
        </div>
      )}

      {resultEntries.length > 0 && (
        <>
          <div className="lmb-tagger-bulk">
            <span style={{fontSize:12,color:'var(--text-muted)'}}>{Object.keys(accepted).length} zaakceptowanych · {Object.keys(rejected).length} odrzuconych</span>
            <div style={{display:'flex',gap:8}}>
              <Btn size="sm" variant="success" onClick={acceptAll}>✓ Zaakceptuj wszystkie</Btn>
              <Btn size="sm" variant="danger" onClick={rejectAll}>✕ Odrzuć wszystkie</Btn>
            </div>
          </div>
          <div className="lmb-tagger-list">
            {resultEntries.map(t => {
              const res = results[t.id];
              const match = res?.bestMatch;
              const isAcc = accepted[t.id], isRej = rejected[t.id];
              return (
                <div key={t.id} className={`lmb-tagger-row ${isAcc?'accepted':''} ${isRej?'rejected':''}`}>
                  <CoverArt track={t} size={36}/>
                  <div style={{flex:1,minWidth:0}}>
                    <div style={{fontWeight:600,marginBottom:4,fontSize:13}}>{t.title} <span style={{color:'var(--text-muted)',fontWeight:400}}>— {t.artist||'?'}</span></div>
                    {res?.error && <div style={{color:'var(--danger)',fontSize:12}}>⚠ {res.error}</div>}
                    {match ? (
                      <>
                        <div style={{fontSize:10,color:'var(--text-muted)',marginBottom:6}}>
                          Źródło: <strong style={{color:'var(--accent)'}}>{match.source}</strong> · Dopasowanie:&nbsp;
                          <span style={{color:match.score>=80?'#39ffb6':match.score>=60?'var(--warn)':'var(--danger)',fontWeight:700}}>{match.score}%</span>
                          {res.suggestions?.length > 1 && <span> · {res.suggestions.length} wyników</span>}
                        </div>
                        <div className="lmb-tagger-fields">
                          {[['Tytuł',t.title,match.title],['Artysta',t.artist,match.artist],['Album',t.album,match.album],['Rok',t.year,match.year],['Gatunek',t.genre,match.genre],['Nastrój',t.mood,match.mood],['BPM',t.bpm,match.bpm]].filter(([,o,n])=>n).map(([label,old,next])=>{
                            const changed = String(old||'') !== String(next||'');
                            return (
                              <div key={label} className={`lmb-tagger-field ${changed?'changed':''}`}>
                                <span className="lmb-tagger-field-label">{label}</span>
                                <span className="lmb-tagger-field-old">{old||'—'}</span>
                                {changed&&<><span className="lmb-tagger-arrow">→</span><span className="lmb-tagger-field-new">{next}</span></>}
                              </div>
                            );
                          })}
                        </div>
                        {res.tags?.length > 0 && (
                          <div style={{display:'flex',gap:4,marginTop:6,flexWrap:'wrap'}}>
                            {res.tags.slice(0,8).map(tag=><Badge key={tag}>#{tag}</Badge>)}
                          </div>
                        )}
                      </>
                    ) : !res?.error && <div style={{color:'var(--text-muted)',fontSize:12}}>Brak wyników</div>}
                  </div>
                  <div style={{display:'flex',flexDirection:'column',gap:6,flexShrink:0,alignItems:'center'}}>
                    {!isAcc&&!isRej&&match&&<>
                      <Btn size="sm" variant="success" onClick={()=>setAccepted(a=>({...a,[t.id]:true}))}>✓</Btn>
                      <Btn size="sm" variant="danger"  onClick={()=>setRejected(r=>({...r,[t.id]:true}))}>✕</Btn>
                    </>}
                    {isAcc&&<span style={{color:'#39ffb6',fontSize:12,fontWeight:700}}>✓</span>}
                    {isRej&&<span style={{color:'var(--danger)',fontSize:12,fontWeight:700}}>✕</span>}
                  </div>
                </div>
              );
            })}
          </div>
          {done && (
            <div style={{display:'flex',justifyContent:'flex-end',gap:8,paddingTop:12,borderTop:'1px solid var(--border)',marginTop:12}}>
              <Btn onClick={onClose}>Anuluj</Btn>
              <Btn variant="primary" onClick={applyAccepted}>Zapisz {Object.keys(accepted).filter(id=>!rejected[id]).length} zaakceptowanych</Btn>
            </div>
          )}
        </>
      )}

      {!running && !done && (
        <div style={{padding:'28px 0',textAlign:'center',color:'var(--text-muted)'}}>
          <div style={{fontSize:40,marginBottom:12}}>🔍</div>
          <div>Wybierz źródła i uruchom wyszukiwanie</div>
          <div style={{fontSize:12,marginTop:8}}>MusicBrainz i Discogs bezpłatne · Last.fm i AI wymagają klucza API</div>
        </div>
      )}
    </Modal>
  );
}

/* ─── SETTINGS ─── */
const DEFAULT_SETTINGS = {
  autoBackup: true, scanSubfolders: true, validationMode: 'balanced',
  namePattern: '{artist} - {title}', folderPattern: '{genre}/{artist}', cacheTTL: 7,
  // API keys
  discogsToken: '', lastfmKey: '',
  openaiKey: '', openaiUrl: 'https://api.openai.com/v1', openaiModel: 'gpt-4o-mini',
  grokKey: '', deepseekKey: '',
  aiProvider: 'openai',
  searchProviders: ['musicbrainz'],
};

function SettingsDialog({ onClose }) {
  const [tab, setTab] = useState('ogolne');
  const [vals, setVals] = useState(() => ({ ...DEFAULT_SETTINGS, ...(window.MetaApi?.loadSettings() || {}) }));
  const set = (k, v) => setVals(s => ({ ...s, [k]: v }));
  const [saved, setSaved] = useState(false);

  const save = () => {
    localStorage.setItem(window.MetaApi?.SETTINGS_KEY || 'lmb_settings', JSON.stringify(vals));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const toggleProvider = id => {
    set('searchProviders', vals.searchProviders.includes(id)
      ? vals.searchProviders.filter(p => p !== id)
      : [...vals.searchProviders, id]);
  };

  return (
    <Modal title="Ustawienia" onClose={onClose} width={680}>
      <Tabs tabs={[
        { id:'ogolne',   label:'Ogólne',     icon:'⚙' },
        { id:'api',      label:'Klucze API',  icon:'🔑' },
        { id:'ai',       label:'Dostawca AI', icon:'✦' },
        { id:'metadane', label:'Metadane',    icon:'📋' },
      ]} active={tab} onChange={setTab}/>

      <div style={{padding:'16px 0', minHeight:280}}>

        {/* ── OGÓLNE ── */}
        {tab==='ogolne' && (
          <div className="lmb-settings-grid">
            {[
              {label:'Auto-backup bazy',    type:'toggle', key:'autoBackup'},
              {label:'Skanuj podfoldery',   type:'toggle', key:'scanSubfolders'},
              {label:'Tryb walidacji',      type:'select', key:'validationMode',
               options:[{value:'strict',label:'Rygorystyczny'},{value:'balanced',label:'Zbalansowany'},{value:'lenient',label:'Łagodny'}]},
            ].map(f => <SettingsField key={f.key} field={f} vals={vals} set={set}/>)}
          </div>
        )}

        {/* ── KLUCZE API ── */}
        {tab==='api' && (
          <div className="lmb-settings-grid">
            <div style={{fontSize:12,color:'var(--text-muted)',lineHeight:1.7,padding:'8px',background:'var(--surface2)',borderRadius:8}}>
              Klucze API są przechowywane <strong>lokalnie</strong> w przeglądarce (localStorage). Nie są wysyłane nigdzie poza wskazany endpoint.
            </div>

            <div className="lmb-settings-section">Discogs</div>
            <SettingsField field={{label:'Token Discogs',type:'password',key:'discogsToken',placeholder:'Discogs Personal Access Token'}} vals={vals} set={set}/>
            <div className="lmb-settings-hint">
              Uzyskaj token na: <a href="https://www.discogs.com/settings/developers" target="_blank" style={{color:'var(--accent)'}}>discogs.com/settings/developers</a>
            </div>

            <div className="lmb-settings-section">Last.fm</div>
            <SettingsField field={{label:'Klucz Last.fm API',type:'password',key:'lastfmKey',placeholder:'Last.fm API Key'}} vals={vals} set={set}/>
            <div className="lmb-settings-hint">
              Zarejestruj aplikację: <a href="https://www.last.fm/api/account/create" target="_blank" style={{color:'var(--accent)'}}>last.fm/api</a>
            </div>

            <div className="lmb-settings-section">OpenAI</div>
            <SettingsField field={{label:'Klucz OpenAI',type:'password',key:'openaiKey',placeholder:'sk-…'}} vals={vals} set={set}/>
            <SettingsField field={{label:'Base URL',type:'text',key:'openaiUrl',placeholder:'https://api.openai.com/v1'}} vals={vals} set={set}/>
            <SettingsField field={{label:'Model',type:'text',key:'openaiModel',placeholder:'gpt-4o-mini'}} vals={vals} set={set}/>

            <div className="lmb-settings-section">Grok (xAI)</div>
            <SettingsField field={{label:'Klucz Grok',type:'password',key:'grokKey',placeholder:'xai-…'}} vals={vals} set={set}/>

            <div className="lmb-settings-section">DeepSeek</div>
            <SettingsField field={{label:'Klucz DeepSeek',type:'password',key:'deepseekKey',placeholder:'sk-…'}} vals={vals} set={set}/>
          </div>
        )}

        {/* ── DOSTAWCA AI ── */}
        {tab==='ai' && (
          <div className="lmb-settings-grid">
            <div className="lmb-settings-section">Domyślny dostawca AI</div>
            <SettingsField field={{label:'Dostawca AI',type:'select',key:'aiProvider',options:[
              {value:'openai',   label:'⚡ OpenAI (GPT-4o-mini)'},
              {value:'grok',     label:'✦ Grok (xAI)'},
              {value:'deepseek', label:'🔷 DeepSeek'},
            ]}} vals={vals} set={set}/>

            <div className="lmb-settings-section">Domyślne źródła wyszukiwania</div>
            <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
              {Object.entries(PROVIDER_LABELS).map(([id,p]) => (
                <button key={id}
                  className={`lmb-provider-btn ${vals.searchProviders.includes(id)?'active':''}`}
                  onClick={()=>toggleProvider(id)}>
                  {p.icon} {p.name} {p.free&&<span style={{fontSize:9,opacity:0.6}}>bezpłatny</span>}
                </button>
              ))}
            </div>
            <div className="lmb-settings-hint">
              Zaznaczone źródła będą domyślnie używane podczas wzbogacania metadanych. Możesz je zmienić bezpośrednio w oknie taggera.
            </div>

            <div className="lmb-settings-section">Status kluczy API</div>
            {[['openai','OpenAI','openaiKey'],['grok','Grok','grokKey'],['deepseek','DeepSeek','deepseekKey'],
              ['discogs','Discogs','discogsToken'],['lastfm','Last.fm','lastfmKey']].map(([id,name,key])=>(
              <div key={id} style={{display:'flex',alignItems:'center',gap:10,padding:'6px 0',borderBottom:'1px solid var(--border)'}}>
                <span style={{width:80,color:'var(--text-muted)',fontSize:12}}>{name}</span>
                <span style={{color:vals[key]?'#39ffb6':'var(--danger)',fontSize:12,fontWeight:600}}>
                  {vals[key]?'✓ skonfigurowany':'✕ brak klucza'}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* ── METADANE ── */}
        {tab==='metadane' && (
          <div className="lmb-settings-grid">
            <div className="lmb-settings-section">Wzorce nazw plików</div>
            {[
              {label:'Wzorzec nazwy',type:'text',key:'namePattern',placeholder:'{artist} - {title}'},
              {label:'Wzorzec folderu',type:'text',key:'folderPattern',placeholder:'{genre}/{artist}'},
            ].map(f=><SettingsField key={f.key} field={f} vals={vals} set={set}/>)}
            <div className="lmb-settings-hint">Tokeny: {'{artist}'} {'{title}'} {'{album}'} {'{year}'} {'{genre}'} {'{bpm}'} {'{key}'}</div>
            <div className="lmb-settings-section">Cache</div>
            <SettingsField field={{label:'TTL cache (dni)',type:'number',key:'cacheTTL'}} vals={vals} set={set}/>
          </div>
        )}
      </div>

      <div style={{display:'flex',justifyContent:'flex-end',gap:8,paddingTop:12,borderTop:'1px solid var(--border)',alignItems:'center'}}>
        {saved && <span style={{color:'#39ffb6',fontSize:12}}>✓ Zapisano</span>}
        <Btn onClick={onClose}>Zamknij</Btn>
        <Btn variant="primary" onClick={save}>Zapisz ustawienia</Btn>
      </div>
    </Modal>
  );
}

function SettingsField({ field, vals, set }) {
  const v = vals[field.key];
  return (
    <div className="lmb-settings-row">
      <label className="lmb-settings-label">{field.label}</label>
      {field.type==='toggle' && (
        <div className={`lmb-toggle ${v?'on':''}`} onClick={()=>set(field.key,!v)}><div className="lmb-toggle-knob"/></div>
      )}
      {field.type==='select' && (
        <Select value={v} onChange={val=>set(field.key,val)} options={field.options}/>
      )}
      {(field.type==='text'||field.type==='number') && (
        <input className="lmb-input" type={field.type} value={v} onChange={e=>set(field.key,e.target.value)} placeholder={field.placeholder} style={{width:220}}/>
      )}
    </div>
  );
}

Object.assign(window, { ImportWizard, AiTaggerDialog, MetaSearchDialog, SettingsDialog });
