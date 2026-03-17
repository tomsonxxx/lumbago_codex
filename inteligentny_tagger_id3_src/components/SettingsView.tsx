import React, { useState } from 'react';
import { ApiKeys, AIProvider } from '../services/aiService';

type SettingsSection = 'general' | 'appearance' | 'notifications' | 'api' | 'security' | 'advanced';

interface SettingsViewProps {
  apiKeys: ApiKeys;
  aiProvider: AIProvider;
  renamePattern: string;
  onSave: (keys: ApiKeys, provider: AIProvider) => void;
  onRenamePatternChange: (pattern: string) => void;
}

const sectionLabels: { id: SettingsSection; label: string }[] = [
  { id: 'general', label: 'Ogólne' },
  { id: 'appearance', label: 'Wygląd' },
  { id: 'notifications', label: 'Powiadomienia' },
  { id: 'api', label: 'Klucze API' },
  { id: 'security', label: 'Zabezpieczenia' },
  { id: 'advanced', label: 'Zaawansowane' },
];

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '10px 14px', borderRadius: 8, fontSize: 13,
  background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
  color: '#e6f7ff', outline: 'none',
};

const SettingsView: React.FC<SettingsViewProps> = ({ apiKeys, aiProvider, renamePattern, onSave, onRenamePatternChange }) => {
  const [activeSection, setActiveSection] = useState<SettingsSection>('api');
  const [localKeys, setLocalKeys] = useState<ApiKeys>(apiKeys);
  const [localProvider, setLocalProvider] = useState<AIProvider>(aiProvider);
  const [localPattern, setLocalPattern] = useState(renamePattern);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    onSave(localKeys, localProvider);
    onRenamePatternChange(localPattern);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const clearStorage = () => {
    if (confirm('Czy na pewno chcesz wyczyścić wszystkie dane lokalnie?')) {
      localStorage.clear();
      window.location.reload();
    }
  };

  const providers: { id: AIProvider; label: string; placeholder: string }[] = [
    { id: 'gemini', label: 'Google Gemini', placeholder: 'AIza...' },
    { id: 'openai', label: 'OpenAI', placeholder: 'sk-...' },
    { id: 'grok', label: 'Grok (xAI)', placeholder: 'xai-...' },
  ];

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', gap: 24 }}>
      {/* Left nav */}
      <nav style={{ width: 180, flexShrink: 0 }}>
        <h3 style={{ color: '#94a3b8', fontSize: 11, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase', margin: '0 0 12px', padding: '0 12px' }}>
          Ustawienia
        </h3>
        {sectionLabels.map(s => (
          <button
            key={s.id}
            onClick={() => setActiveSection(s.id)}
            style={{
              display: 'block', width: '100%', textAlign: 'left',
              padding: '9px 14px', borderRadius: 8, fontSize: 13, marginBottom: 2,
              background: activeSection === s.id ? 'rgba(0,212,255,0.1)' : 'transparent',
              border: `1px solid ${activeSection === s.id ? 'rgba(0,212,255,0.3)' : 'transparent'}`,
              color: activeSection === s.id ? '#00d4ff' : '#94a3b8',
              cursor: 'pointer', transition: 'all 0.15s',
              fontWeight: activeSection === s.id ? 600 : 400,
            }}
          >
            {s.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <div style={{
        flex: 1,
        background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(0,212,255,0.15)',
        borderRadius: 16, padding: 28,
      }}>
        {activeSection === 'api' && (
          <>
            <h2 style={{ color: '#e6f7ff', fontSize: 18, fontWeight: 600, margin: '0 0 24px' }}>Klucze API</h2>

            {/* Provider selection */}
            <div style={{ marginBottom: 24 }}>
              <label style={{ fontSize: 12, color: '#94a3b8', display: 'block', marginBottom: 10 }}>Wybór dostawcy AI</label>
              <div style={{ display: 'flex', gap: 8 }}>
                {providers.map(p => (
                  <button key={p.id} onClick={() => setLocalProvider(p.id)}
                    style={{
                      flex: 1, padding: '9px 12px', borderRadius: 8, fontSize: 12, fontWeight: 600,
                      background: localProvider === p.id ? 'rgba(0,212,255,0.15)' : 'rgba(255,255,255,0.04)',
                      border: `1px solid ${localProvider === p.id ? '#00d4ff' : 'rgba(255,255,255,0.08)'}`,
                      color: localProvider === p.id ? '#00d4ff' : '#94a3b8',
                      cursor: 'pointer', transition: 'all 0.15s',
                    }}>
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* API key inputs */}
            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 12, color: '#94a3b8', display: 'block', marginBottom: 8 }}>Klucz API</label>
              <input
                type="password"
                value={localProvider === 'openai' ? localKeys.openai : localKeys.grok}
                onChange={e => setLocalKeys(k => localProvider === 'openai' ? { ...k, openai: e.target.value } : { ...k, grok: e.target.value })}
                placeholder={providers.find(p => p.id === localProvider)?.placeholder || 'Klucz API...'}
                className="input-dark"
                style={inputStyle}
              />
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 12, color: '#94a3b8', display: 'block', marginBottom: 8 }}>Klucz API pomocniczy (OpenAI)</label>
              <input
                type="password"
                value={localKeys.openai}
                onChange={e => setLocalKeys(k => ({ ...k, openai: e.target.value }))}
                placeholder="sk-..."
                className="input-dark"
                style={inputStyle}
              />
            </div>

            <div style={{ marginBottom: 28 }}>
              <label style={{ fontSize: 12, color: '#94a3b8', display: 'block', marginBottom: 8 }}>Wybór modelu</label>
              <select className="input-dark" style={inputStyle}>
                <option>Wybierz model</option>
                <option>gemini-2.0-flash-exp</option>
                <option>gpt-4o-mini</option>
                <option>grok-beta</option>
              </select>
            </div>

            <button onClick={handleSave} className="btn-cta"
              style={{ padding: '12px 32px', borderRadius: 8, fontSize: 14, fontWeight: 700, minWidth: 140 }}>
              {saved ? '✓ Zapisano!' : 'Zapisz'}
            </button>
          </>
        )}

        {activeSection === 'general' && (
          <>
            <h2 style={{ color: '#e6f7ff', fontSize: 18, fontWeight: 600, margin: '0 0 24px' }}>Ogólne</h2>

            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 12, color: '#94a3b8', display: 'block', marginBottom: 8 }}>Szablon nazw plików</label>
              <input
                type="text"
                value={localPattern}
                onChange={e => setLocalPattern(e.target.value)}
                className="input-dark"
                style={inputStyle}
                placeholder="[artist] - [title]"
              />
              <p style={{ fontSize: 11, color: '#64748b', marginTop: 6 }}>
                Dostępne zmienne: [artist], [title], [album], [year], [genre], [track]
              </p>
            </div>

            <button onClick={handleSave} className="btn-cta"
              style={{ padding: '12px 32px', borderRadius: 8, fontSize: 14, fontWeight: 700 }}>
              {saved ? '✓ Zapisano!' : 'Zapisz'}
            </button>
          </>
        )}

        {activeSection === 'appearance' && (
          <>
            <h2 style={{ color: '#e6f7ff', fontSize: 18, fontWeight: 600, margin: '0 0 24px' }}>Wygląd</h2>
            <div style={{ padding: '20px 0', color: '#94a3b8', fontSize: 13 }}>
              <p>Motyw: <strong style={{ color: '#00d4ff' }}>Dark / Neon</strong> (domyślny)</p>
              <p style={{ marginTop: 10 }}>Interfejs używa futurystycznej palety kolorów z akcentami cyan i fioletowym.</p>
            </div>
          </>
        )}

        {activeSection === 'notifications' && (
          <>
            <h2 style={{ color: '#e6f7ff', fontSize: 18, fontWeight: 600, margin: '0 0 24px' }}>Powiadomienia</h2>
            <div style={{ color: '#94a3b8', fontSize: 13 }}>
              Powiadomienia są wyświetlane w panelu aktywności na stronie głównej.
            </div>
          </>
        )}

        {activeSection === 'security' && (
          <>
            <h2 style={{ color: '#e6f7ff', fontSize: 18, fontWeight: 600, margin: '0 0 24px' }}>Zabezpieczenia</h2>
            <div style={{ color: '#94a3b8', fontSize: 13 }}>
              <p>Klucze API są przechowywane lokalnie w przeglądarce (localStorage).</p>
              <p style={{ marginTop: 10 }}>Dane nie są przesyłane na żaden zewnętrzny serwer poza bezpośrednimi wywołaniami API.</p>
            </div>
          </>
        )}

        {activeSection === 'advanced' && (
          <>
            <h2 style={{ color: '#e6f7ff', fontSize: 18, fontWeight: 600, margin: '0 0 24px' }}>Zaawansowane</h2>
            <div style={{ marginBottom: 20 }}>
              <h4 style={{ color: '#e6f7ff', fontSize: 14, margin: '0 0 10px' }}>Dane lokalne</h4>
              <button onClick={clearStorage}
                style={{ padding: '10px 20px', borderRadius: 8, fontSize: 13, background: 'rgba(236,72,153,0.15)', border: '1px solid rgba(236,72,153,0.3)', color: '#ec4899', cursor: 'pointer' }}>
                Wyczyść wszystkie dane
              </button>
              <p style={{ fontSize: 11, color: '#64748b', marginTop: 8 }}>
                Usuwa całą bibliotekę, klucze API i ustawienia z przeglądarki.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SettingsView;
