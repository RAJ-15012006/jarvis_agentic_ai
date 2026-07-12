import React, { useState, useRef } from 'react';

const BASE_URL = window.location.origin.includes('localhost')
  ? 'http://localhost:8000'
  : window.location.origin;

const genderConfig = {
  Boy:  { color: '#38bdf8', label: 'MALE / BOY',   icon: '♂', glow: 'rgba(56,189,248,0.35)' },
  Girl: { color: '#f472b6', label: 'FEMALE / GIRL', icon: '♀', glow: 'rgba(244,114,182,0.35)' },
  Multiple:          { color: '#a78bfa', label: 'MULTIPLE', icon: '⚧', glow: 'rgba(167,139,250,0.35)' },
  Object:            { color: '#00ffc9', label: 'OBJECT',   icon: '📦', glow: 'rgba(0,255,201,0.35)' },
  Scene:             { color: '#34d399', label: 'ENVIRONMENT', icon: '🏞️', glow: 'rgba(52,211,153,0.35)' },
  Text:              { color: '#fbbf24', label: 'TEXT / DOC',  icon: '📄', glow: 'rgba(251,191,36,0.35)' },
  Animal:            { color: '#fb7185', label: 'ANIMAL',      icon: '🐾', glow: 'rgba(251,113,133,0.35)' },
  Unclear:           { color: '#94a3b8', label: 'UNCLEAR',  icon: '?', glow: 'rgba(148,163,184,0.25)' },
  'No Person Detected': { color: '#f87171', label: 'NO PERSON', icon: '✗', glow: 'rgba(248,113,113,0.25)' },
};

const confidenceColor = { High: '#4ade80', Medium: '#facc15', Low: '#f87171' };

export const GenderDetection = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (f) => {
    if (!f) return;
    const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowed.includes(f.type)) {
      setError('Only JPG, PNG, WEBP images allowed.');
      return;
    }
    setFile(f);
    setError(null);
    setResult(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(f);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${BASE_URL}/api/analyze-gender`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        setResult(data.result);
      } else {
        setError(data.error || 'Analysis failed. Please try again.');
      }
    } catch {
      setError('Connection to JARVIS Core failed.');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
  };

  const cfg = result ? (genderConfig[result.gender] || genderConfig['Unclear']) : null;

  return (
    <div className="border border-jarvis-cyan/30 bg-black/60 rounded-lg p-4 shadow-[0_0_15px_rgba(0,255,209,0.05)] text-jarvis-cyan backdrop-blur-sm">
      <h3 className="font-orbitron text-xs tracking-widest font-bold text-center mb-3">
        INTELLIGENT · VISION SCAN
      </h3>

      {/* Drop zone */}
      {!preview && (
        <label
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={`w-full flex flex-col items-center justify-center border border-dashed rounded-lg p-4 cursor-pointer transition-all ${
            dragging
              ? 'border-jarvis-cyan bg-jarvis-cyan/10'
              : 'border-jarvis-cyan/30 hover:bg-jarvis-cyan/5'
          }`}
        >
          {/* Scan icons decorative */}
          <div className="flex gap-3 mb-2 items-center">
            <span className="text-[#38bdf8] text-lg font-bold">♂</span>
            <span className="text-[#f472b6] text-lg font-bold">♀</span>
            <span className="text-jarvis-cyan/40 text-xs">|</span>
            <span className="text-jarvis-cyan text-lg">📦</span>
            <span className="text-[#fbbf24] text-lg">📄</span>
          </div>
          <span className="font-mono text-xs tracking-wider text-jarvis-cyan/80 text-center">
            UPLOAD IMAGE TO SCAN
          </span>
          <span className="font-mono text-[10px] text-jarvis-cyan/40 mt-1">
            JPG · PNG · WEBP
          </span>
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/jpg,image/png,image/webp"
            onChange={(e) => handleFile(e.target.files?.[0])}
            className="hidden"
          />
        </label>
      )}

      {/* Preview */}
      {preview && !result && (
        <div className="flex flex-col items-center gap-3">
          <div
            className="relative w-full rounded-lg overflow-hidden border border-jarvis-cyan/30"
            style={{ maxHeight: 140 }}
          >
            <img
              src={preview}
              alt="Scan target"
              className="w-full object-cover"
              style={{ maxHeight: 140 }}
            />
            {/* Scan line animation */}
            {loading && (
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  background: 'linear-gradient(to bottom, transparent 48%, rgba(0,255,209,0.25) 50%, transparent 52%)',
                  animation: 'scanline 1.5s linear infinite',
                }}
              />
            )}
            <button
              onClick={reset}
              className="absolute top-1 right-1 bg-black/70 border border-jarvis-cyan/30 text-jarvis-cyan/60 hover:text-white rounded-full w-5 h-5 text-xs flex items-center justify-center transition-all"
            >
              ×
            </button>
          </div>
          <span className="font-mono text-[10px] text-jarvis-cyan/50 truncate w-full text-center">
            {file?.name}
          </span>
          {!loading ? (
            <button
              onClick={handleAnalyze}
              className="w-full py-1.5 border border-jarvis-cyan text-jarvis-cyan font-orbitron text-xs hover:bg-jarvis-cyan hover:text-black rounded transition-all tracking-wider"
            >
              INITIATE SCAN
            </button>
          ) : (
            <div className="flex items-center gap-2 py-1">
              <div className="w-4 h-4 border-2 border-jarvis-cyan border-t-transparent animate-spin rounded-full" />
              <span className="font-mono text-xs tracking-widest animate-pulse">SCANNING...</span>
            </div>
          )}
        </div>
      )}

      {/* Result */}
      {result && cfg && (
        <div className="flex flex-col gap-2">
          {/* Preview thumbnail */}
          {preview && (
            <img
              src={preview}
              alt="Scanned"
              className="w-full rounded-lg object-cover border border-jarvis-cyan/20"
              style={{ maxHeight: 100 }}
            />
          )}

          {/* Gender badge */}
          <div
            className="flex flex-col items-center py-3 rounded-lg border"
            style={{
              borderColor: cfg.color + '55',
              background: `radial-gradient(ellipse at center, ${cfg.glow} 0%, transparent 70%)`,
              boxShadow: `0 0 18px ${cfg.glow}`,
            }}
          >
            <span style={{ color: cfg.color, fontSize: 28, lineHeight: 1 }}>{cfg.icon}</span>
            <span
              className="font-orbitron text-sm font-bold tracking-widest mt-1"
              style={{ color: cfg.color }}
            >
              {cfg.label}
            </span>

            {/* Confidence bar */}
            <div className="flex items-center gap-2 mt-2">
              <span className="font-mono text-[10px] text-jarvis-cyan/50">CONFIDENCE</span>
              <span
                className="font-orbitron text-[10px] tracking-wider px-2 py-0.5 rounded border"
                style={{
                  color: confidenceColor[result.confidence] || '#94a3b8',
                  borderColor: (confidenceColor[result.confidence] || '#94a3b8') + '55',
                }}
              >
                {result.confidence || 'N/A'}
              </span>
              {result.count != null && (
                <span className="font-mono text-[10px] text-jarvis-cyan/50">
                  · {result.count} DETECTED
                </span>
              )}
            </div>
          </div>

          {/* Description */}
          {result.description && (
            <p className="font-mono text-[10px] text-jarvis-cyan/70 leading-relaxed text-center">
              {result.description}
            </p>
          )}

          {/* Visual cues */}
          {result.details?.length > 0 && (
            <div className="flex flex-wrap gap-1 justify-center">
              {result.details.map((d, i) => (
                <span
                  key={i}
                  className="font-mono text-[9px] px-1.5 py-0.5 border border-jarvis-cyan/20 rounded text-jarvis-cyan/60 bg-jarvis-cyan/5"
                >
                  {d}
                </span>
              ))}
            </div>
          )}

          {/* Scan again button */}
          <button
            onClick={reset}
            className="w-full py-1 border border-jarvis-cyan/30 text-jarvis-cyan/60 font-orbitron text-[10px] hover:border-jarvis-cyan/60 hover:text-jarvis-cyan rounded transition-all tracking-wider mt-1"
          >
            NEW SCAN
          </button>
        </div>
      )}

      {error && (
        <div className="text-red-400 font-mono text-[10px] text-center border border-red-500/20 bg-red-950/20 p-2 rounded mt-2">
          {error}
        </div>
      )}

      <style>{`
        @keyframes scanline {
          0%   { transform: translateY(-100%); }
          100% { transform: translateY(200%); }
        }
      `}</style>
    </div>
  );
};
