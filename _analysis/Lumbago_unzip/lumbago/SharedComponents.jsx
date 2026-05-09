// Lumbago — Shared UI Primitives
const { useState, useEffect, useRef } = React;

function Btn({ children, variant="default", size="md", onClick, disabled, className="", title }) {
  const base = "lmb-btn";
  return (
    <button
      className={`${base} ${base}--${variant} ${base}--${size} ${className}`}
      onClick={onClick} disabled={disabled} title={title}
    >{children}</button>
  );
}

function Badge({ children, color }) {
  return <span className="lmb-badge" style={color ? {background: color+'22', color, border:`1px solid ${color}44`} : {}}>{children}</span>;
}

function Modal({ title, onClose, children, width=640, noPad }) {
  useEffect(() => {
    const fn = e => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', fn);
    return () => document.removeEventListener('keydown', fn);
  }, [onClose]);
  return (
    <div className="lmb-modal-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="lmb-modal" style={{width, maxWidth:'95vw'}}>
        <div className="lmb-modal-header">
          <span className="lmb-modal-title">{title}</span>
          <button className="lmb-modal-close" onClick={onClose}>✕</button>
        </div>
        <div className={noPad ? "" : "lmb-modal-body"}>{children}</div>
      </div>
    </div>
  );
}

function ProgressBar({ value, max=100, label, color }) {
  const pct = Math.round((value/max)*100);
  return (
    <div className="lmb-progress">
      <div className="lmb-progress-track">
        <div className="lmb-progress-fill" style={{width:`${pct}%`, background: color || 'var(--accent)'}} />
      </div>
      {label && <span className="lmb-progress-label">{label}</span>}
    </div>
  );
}

function Tabs({ tabs, active, onChange }) {
  return (
    <div className="lmb-tabs">
      {tabs.map(t => (
        <button key={t.id} className={`lmb-tab ${active===t.id?'lmb-tab--active':''}`} onClick={()=>onChange(t.id)}>
          {t.icon && <span>{t.icon}</span>} {t.label}
        </button>
      ))}
    </div>
  );
}

function Select({ value, onChange, options }) {
  return (
    <select className="lmb-select" value={value} onChange={e=>onChange(e.target.value)}>
      {options.map(o => <option key={o.value||o} value={o.value||o}>{o.label||o}</option>)}
    </select>
  );
}

function Input({ value, onChange, placeholder, type="text" }) {
  return (
    <input className="lmb-input" type={type} value={value} onChange={e=>onChange(e.target.value)} placeholder={placeholder} />
  );
}

function KeyBadge({ k }) {
  const colors = { "1A":"#ff6bd5","2A":"#ff6bd5","3A":"#c77dff","4A":"#c77dff","5A":"#63f2ff","6A":"#63f2ff","7A":"#39ffb6","8A":"#39ffb6","9A":"#f7c26a","10A":"#f7c26a","11A":"#ff9f68","12A":"#ff9f68","1B":"#ff6bd5","2B":"#ff6bd5","3B":"#c77dff","4B":"#c77dff","5B":"#63f2ff","6B":"#63f2ff","7B":"#39ffb6","8B":"#39ffb6","9B":"#f7c26a","10B":"#f7c26a","11B":"#ff9f68","12B":"#ff9f68" };
  const c = colors[k] || '#8fb8d8';
  return <span className="lmb-key-badge" style={{color:c, borderColor:c+'44', background:c+'15'}}>{k}</span>;
}

function StarRating({ value }) {
  return (
    <span className="lmb-stars">
      {[1,2,3,4,5].map(i => <span key={i} style={{color: i<=value ? '#f7c26a' : '#2b3a55'}}>★</span>)}
    </span>
  );
}

function ConfidenceDot({ value }) {
  if (value == null) return <span style={{color:'var(--text-muted)', fontSize:11}}>—</span>;
  const pct = Math.round(value * 100);
  const color = pct >= 90 ? '#39ffb6' : pct >= 70 ? '#f7c26a' : '#ff6b6b';
  return <span style={{color, fontSize:11, fontWeight:600}}>{pct}%</span>;
}

function WaveformPlaceholder({ progress=0 }) {
  const bars = 60;
  const heights = Array.from({length:bars}, (_,i) => {
    const x = i/bars;
    return 15 + Math.abs(Math.sin(x*12.3)*25 + Math.sin(x*7.7)*18 + Math.sin(x*3.1)*10);
  });
  return (
    <div className="lmb-waveform">
      {heights.map((h,i) => {
        const done = (i/bars) < progress;
        return <div key={i} className="lmb-waveform-bar" style={{height:h, background: done ? 'var(--accent)' : 'var(--border-accent)'}} />;
      })}
    </div>
  );
}

Object.assign(window, { Btn, Badge, Modal, ProgressBar, Tabs, Select, Input, KeyBadge, StarRating, ConfidenceDot, WaveformPlaceholder });
