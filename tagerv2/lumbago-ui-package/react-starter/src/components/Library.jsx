import React from 'react';

export default function Library() {
  const tracks = [
    { title: "Midnight City", artist: "M83", bpm: 105, key: "6A" },
    { title: "Strobe", artist: "Deadmau5", bpm: 128, key: "9B" },
    { title: "Glue", artist: "Bicep", bpm: 130, key: "4A" },
  ];

  return (
    <div style={{ flex: 1, padding: '30px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h1>Library</h1>
        <button className="btn btn-primary">Import</button>
      </div>
      <div className="card">
        {tracks.map((t, i) => (
          <div key={i} className="table-row">
            <div style={{ flex: 2 }}>{t.title}</div>
            <div style={{ flex: 1, color: 'var(--text-secondary)' }}>{t.artist}</div>
            <div style={{ width: 80 }}><span className="tag tag-bpm">{t.bpm}</span></div>
            <div style={{ width: 60 }}><span className="tag tag-key">{t.key}</span></div>
          </div>
        ))}
      </div>
    </div>
  );
}