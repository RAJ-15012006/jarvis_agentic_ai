import React, { useState, useEffect, useCallback, useRef } from 'react';

// ─── Emotion configs ────────────────────────────────────────────────────────
const EMOTION_CONFIG = {
  happy:     { emoji: '😊', color: '#ffd700', label: 'HAPPY',     glow: '#ffd70066' },
  sad:       { emoji: '💙', color: '#60a5fa', label: 'SAD',       glow: '#60a5fa44' },
  angry:     { emoji: '🔴', color: '#ef4444', label: 'ANGRY',     glow: '#ef444455' },
  surprised: { emoji: '😲', color: '#a78bfa', label: 'SURPRISED', glow: '#a78bfa44' },
  fearful:   { emoji: '🛡️', color: '#f97316', label: 'FEARFUL',   glow: '#f9731644' },
  disgusted: { emoji: '😤', color: '#84cc16', label: 'DISGUSTED', glow: '#84cc1644' },
  stressed:  { emoji: '😓', color: '#fb923c', label: 'STRESSED',  glow: '#fb923c44' },
  neutral:   { emoji: '🤖', color: '#00d4ff', label: 'NEUTRAL',   glow: '#00d4ff33' },
};

// ─── Radial confidence ring ─────────────────────────────────────────────────
function ConfidenceRing({ confidence = 0.5, emotion = 'neutral', size = 80 }) {
  const cfg = EMOTION_CONFIG[emotion] || EMOTION_CONFIG.neutral;
  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - confidence * circumference;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
      <svg width={size} height={size} style={{ filter: `drop-shadow(0 0 6px ${cfg.glow})` }}>
        <circle cx={size/2} cy={size/2} r={radius}
          fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
        <circle cx={size/2} cy={size/2} r={radius}
          fill="none" stroke={cfg.color} strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transform: 'rotate(-90deg)',
            transformOrigin: '50% 50%',
            transition: 'stroke-dashoffset 0.8s ease, stroke 0.5s ease',
          }}
        />
        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle"
          fontSize="22" style={{ userSelect: 'none' }}>
          {cfg.emoji}
        </text>
      </svg>
      <span style={{ fontSize: '9px', color: cfg.color, fontWeight: '700', letterSpacing: '1.5px' }}>
        {cfg.label}
      </span>
      <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', fontFamily: 'monospace' }}>
        {(confidence * 100).toFixed(0)}%
      </span>
    </div>
  );
}

// ─── Emotion History Chart ──────────────────────────────────────────────────
function EmotionHistory({ history }) {
  if (!history.length) return null;
  return (
    <div style={{ display: 'flex', gap: '4px', alignItems: 'flex-end', height: '30px', padding: '0 2px' }}>
      {history.slice(-12).map((e, i) => {
        const cfg = EMOTION_CONFIG[e.emotion] || EMOTION_CONFIG.neutral;
        return (
          <div key={i} title={`${e.emotion} ${Math.round(e.confidence * 100)}%`}
            style={{
              flex: 1, borderRadius: '2px',
              background: cfg.color,
              height: `${Math.max(4, e.confidence * 30)}px`,
              opacity: 0.7 + (i / history.length) * 0.3,
              transition: 'height 0.3s',
            }}
          />
        );
      })}
    </div>
  );
}

// ─── Suggestion Banner ──────────────────────────────────────────────────────
function SuggestionBanner({ suggestion, emotion }) {
  if (!suggestion) return null;
  const cfg = EMOTION_CONFIG[emotion] || EMOTION_CONFIG.neutral;
  return (
    <div style={{
      background: `${cfg.color}15`,
      border: `1px solid ${cfg.color}33`,
      borderRadius: '8px',
      padding: '8px 10px',
      fontSize: '11px',
      color: cfg.color,
      marginTop: '8px',
      animation: 'fadeInBanner 0.4s ease',
    }}>
      💬 {suggestion}
      <style>{`@keyframes fadeInBanner { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }`}</style>
    </div>
  );
}

// ─── Main Emotion Widget ────────────────────────────────────────────────────
export function EmotionWidget({ socket }) {
  const [emotion, setEmotion] = useState('neutral');
  const [confidence, setConfidence] = useState(0.5);
  const [suggestion, setSuggestion] = useState(null);
  const [style, setStyle] = useState('professional');
  const [scanning, setScanning] = useState(false);
  const [history, setHistory] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoScan, setAutoScan] = useState(false);
  const autoScanRef = useRef(null);

  const fetchEmotionState = useCallback(async () => {
    try {
      const res = await fetch('/api/emotion-state');
      const data = await res.json();
      if (data.success && data.emotion) {
        setEmotion(data.emotion);
        setConfidence(data.confidence || 0.5);
        setSuggestion(data.suggestion || null);
        setStyle(data.style || 'professional');
        setLastUpdated(new Date().toLocaleTimeString());
        setHistory(prev => [...prev.slice(-11), { emotion: data.emotion, confidence: data.confidence }]);
      }
    } catch {
      // Silent fail
    }
  }, []);

  // Listen for real-time emotion updates from WebSocket
  useEffect(() => {
    if (!socket) return;
    const handler = (data) => {
      if (data.emotion) {
        setEmotion(data.emotion);
        setConfidence(data.confidence || 0.5);
        setSuggestion(data.suggestion || null);
        setStyle(data.style || 'professional');
        setHistory(prev => [...prev.slice(-11), { emotion: data.emotion, confidence: data.confidence }]);
        setLastUpdated(new Date().toLocaleTimeString());
      }
    };
    socket.on('emotion_update', handler);
    return () => socket.off('emotion_update', handler);
  }, [socket]);

  // Auto-scan every 60s if enabled
  useEffect(() => {
    if (autoScan) {
      autoScanRef.current = setInterval(() => {
        triggerScan();
      }, 60000);
    }
    return () => clearInterval(autoScanRef.current);
  }, [autoScan]);

  const triggerScan = useCallback(() => {
    if (!socket || scanning) return;
    setScanning(true);
    socket.emit('process_command', { command: 'detect my emotion', audio: '' });
    setTimeout(() => {
      fetchEmotionState();
      setScanning(false);
    }, 4000);
  }, [socket, scanning, fetchEmotionState]);

  const cfg = EMOTION_CONFIG[emotion] || EMOTION_CONFIG.neutral;

  // Map style to a HUD label
  const styleLabel = {
    professional: '⚡ Standard Mode',
    gentle: '💙 Gentle Mode',
    calm: '😌 Calm Mode',
    enthusiastic: '🔥 Enthusiastic Mode',
    supportive: '🤝 Supportive Mode',
    reassuring: '🛡️ Secure Mode',
    attentive: '👁️ Attentive Mode',
    direct: '💬 Direct Mode',
  }[style] || '⚡ Standard Mode';

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(0,0,0,0.95), rgba(5,0,20,0.98))',
      border: `1px solid ${cfg.color}33`,
      borderRadius: '14px',
      padding: '14px',
      fontFamily: "'Inter', sans-serif",
      color: '#fff',
      boxShadow: `0 0 20px ${cfg.glow}`,
      transition: 'box-shadow 0.5s ease, border-color 0.5s ease',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Top accent */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
        background: `linear-gradient(90deg, transparent, ${cfg.color}, transparent)`,
        transition: 'background 0.5s ease',
      }} />

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div>
          <div style={{ fontSize: '10px', fontWeight: '700', letterSpacing: '2px', color: cfg.color, textTransform: 'uppercase' }}>
            🎭 EMOTION AI
          </div>
          <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.3)', marginTop: '2px' }}>
            {styleLabel}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            onClick={() => setAutoScan(p => !p)}
            title={autoScan ? "Disable auto-scan" : "Enable auto-scan every 60s"}
            style={{
              background: autoScan ? `${cfg.color}22` : 'transparent',
              border: `1px solid ${autoScan ? cfg.color : 'rgba(255,255,255,0.1)'}44`,
              borderRadius: '5px', padding: '2px 6px',
              cursor: 'pointer', fontSize: '8px',
              color: autoScan ? cfg.color : 'rgba(255,255,255,0.3)',
              letterSpacing: '1px',
            }}
          >
            {autoScan ? '🔄 AUTO' : '⚪ AUTO'}
          </button>
        </div>
      </div>

      {/* Main Emotion Ring */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
        <ConfidenceRing confidence={confidence} emotion={emotion} size={90} />
      </div>

      {/* Emotion History */}
      <div style={{
        background: 'rgba(255,255,255,0.03)', borderRadius: '8px',
        padding: '8px', marginBottom: '10px',
      }}>
        <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.3)', letterSpacing: '1px', marginBottom: '6px', textTransform: 'uppercase' }}>
          Emotion History
        </div>
        <EmotionHistory history={history} />
        {history.length === 0 && (
          <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.2)', textAlign: 'center', padding: '4px' }}>
            Scan to build history
          </div>
        )}
      </div>

      {/* Scan Button */}
      <button
        onClick={triggerScan}
        disabled={scanning}
        style={{
          width: '100%',
          background: scanning
            ? 'rgba(255,255,255,0.04)'
            : `linear-gradient(135deg, ${cfg.color}22, ${cfg.color}11)`,
          border: `1px solid ${cfg.color}44`,
          borderRadius: '8px',
          padding: '8px',
          cursor: scanning ? 'wait' : 'pointer',
          color: scanning ? 'rgba(255,255,255,0.4)' : cfg.color,
          fontSize: '11px',
          fontWeight: '700',
          letterSpacing: '1px',
          textTransform: 'uppercase',
          transition: 'all 0.2s',
          marginBottom: '8px',
        }}
      >
        {scanning ? '⏳ Scanning Webcam...' : '📷 Scan My Emotion'}
      </button>

      {/* Suggestion */}
      <SuggestionBanner suggestion={suggestion} emotion={emotion} />

      {lastUpdated && (
        <div style={{ marginTop: '8px', fontSize: '9px', color: 'rgba(255,255,255,0.2)', textAlign: 'center' }}>
          Last scan: {lastUpdated}
        </div>
      )}
    </div>
  );
}

export default EmotionWidget;
