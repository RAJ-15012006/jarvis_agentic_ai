import React, { useState, useEffect, useRef, useCallback } from 'react';

// ─── Utility: format timestamp ───────────────────────────────────────────────
const fmtTime = (ts) => {
  if (!ts) return '—';
  return ts;
};

// ─── Mini Audio Visualizer ────────────────────────────────────────────────────
function AudioVisualizer({ active }) {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    if (!active) {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawIdle(ctx, canvas.width, canvas.height);
      }
      return;
    }

    let audioCtx;
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      streamRef.current = stream;
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      analyserRef.current = analyser;

      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const W = canvas.width;
      const H = canvas.height;
      const bufLen = analyser.frequencyBinCount;
      const dataArr = new Uint8Array(bufLen);

      const draw = () => {
        animRef.current = requestAnimationFrame(draw);
        analyser.getByteFrequencyData(dataArr);

        ctx.clearRect(0, 0, W, H);
        const barW = (W / bufLen) * 2.5;
        let x = 0;
        for (let i = 0; i < bufLen; i++) {
          const barH = (dataArr[i] / 255) * H;
          const hue = 120 + (dataArr[i] / 255) * 60;
          ctx.fillStyle = `hsla(${hue}, 100%, 55%, 0.85)`;
          ctx.fillRect(x, H - barH, barW - 1, barH);
          x += barW;
        }
      };
      draw();
    }).catch(() => {
      // No mic access — draw idle
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        drawIdle(ctx, canvas.width, canvas.height);
      }
    });

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      if (audioCtx) audioCtx.close();
    };
  }, [active]);

  function drawIdle(ctx, W, H) {
    ctx.strokeStyle = 'rgba(0, 212, 255, 0.25)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, H / 2);
    for (let x = 0; x < W; x++) {
      ctx.lineTo(x, H / 2 + Math.sin(x * 0.15) * 4);
    }
    ctx.stroke();
  }

  return (
    <canvas
      ref={canvasRef}
      width={260}
      height={50}
      style={{
        width: '100%',
        height: '50px',
        borderRadius: '6px',
        background: 'rgba(0,0,0,0.3)',
        display: 'block',
      }}
    />
  );
}

// ─── Circular Score Gauge ─────────────────────────────────────────────────────
function ScoreGauge({ score, label, color, size = 80 }) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
      <svg width={size} height={size}>
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8"
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={color} strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%', transition: 'stroke-dashoffset 0.6s ease' }}
        />
        <text
          x="50%" y="50%"
          textAnchor="middle" dominantBaseline="middle"
          fill={color} fontSize="13" fontWeight="700" fontFamily="'Inter', monospace"
        >
          {Math.round(score)}%
        </text>
      </svg>
      <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', letterSpacing: '1px', textTransform: 'uppercase' }}>
        {label}
      </span>
    </div>
  );
}

// ─── Intruder Event Row ────────────────────────────────────────────────────────
function IntruderRow({ event, index }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      onClick={() => setExpanded(p => !p)}
      style={{
        background: expanded ? 'rgba(255, 40, 40, 0.12)' : 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,40,40,0.2)',
        borderRadius: '8px',
        padding: '10px 14px',
        cursor: 'pointer',
        transition: 'all 0.2s',
        marginBottom: '6px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '18px' }}>📸</span>
          <div>
            <div style={{ fontSize: '12px', color: '#ff6b6b', fontWeight: '600', fontFamily: 'monospace' }}>
              INTRUDER DETECTED #{index + 1}
            </div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.45)', marginTop: '2px' }}>
              {fmtTime(event.timestamp)}
            </div>
          </div>
        </div>
        <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)' }}>{expanded ? '▲' : '▼'}</span>
      </div>

      {expanded && (
        <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid rgba(255,40,40,0.15)' }}>
          <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.35)', fontFamily: 'monospace', wordBreak: 'break-all' }}>
            {event.path}
          </div>
          <div style={{ marginTop: '8px', color: '#ff8585', fontSize: '11px' }}>
            ⚠️ Unauthorized access attempt logged and screen locked.
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export function BiometricsDashboard({ socket, voiceScore = null, faceScore = null }) {
  const [intruderEvents, setIntruderEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [threshold, setThreshold] = useState(82);
  const [voiceActive, setVoiceActive] = useState(false);
  const [faceMode, setFaceMode] = useState('—');
  const [registering, setRegistering] = useState(false);
  const [regStatus, setRegStatus] = useState(null);
  const [liveVoiceScore, setLiveVoiceScore] = useState(voiceScore);
  const [liveFaceScore, setLiveFaceScore] = useState(faceScore);
  const [lastAuthTime, setLastAuthTime] = useState(null);
  const [authStatus, setAuthStatus] = useState('STANDBY'); // STANDBY | VERIFIED | REJECTED

  // Fetch intruder log
  const fetchLog = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/intruder-log');
      const data = await res.json();
      if (data.success) setIntruderEvents(data.events);
    } catch (_) {
      // Silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLog();
    const timer = setInterval(fetchLog, 15000); // auto-refresh every 15s
    return () => clearInterval(timer);
  }, [fetchLog]);

  // Listen for real-time intruder alerts from server
  useEffect(() => {
    if (!socket) return;
    const handler = (data) => {
      setAuthStatus('REJECTED');
      setLastAuthTime(new Date().toLocaleTimeString());
      if (data.score !== undefined) setLiveVoiceScore(data.score * 100);
      // Refresh log after a short delay
      setTimeout(fetchLog, 1000);
    };
    socket.on('intruder_alert', handler);
    return () => socket.off('intruder_alert', handler);
  }, [socket, fetchLog]);

  // Register face handler
  const handleFaceRegister = async () => {
    setRegistering(true);
    setRegStatus(null);
    try {
      const res = await fetch('/api/face-register', { method: 'POST' });
      const data = await res.json();
      setRegStatus(data.success
        ? `✅ Face registered! ${data.samples_captured} samples captured.`
        : `❌ Registration failed: ${data.error || 'Unknown error'}`
      );
      if (data.success) setFaceMode('lbph');
    } catch (e) {
      setRegStatus('❌ Network error during registration.');
    } finally {
      setRegistering(false);
    }
  };

  // Derived security scores
  const voiceScoreDisplay = liveVoiceScore !== null ? Math.min(100, Math.max(0, liveVoiceScore * 100)) : 0;
  const faceScoreDisplay = liveFaceScore !== null ? Math.min(100, Math.max(0, liveFaceScore)) : 0;
  const overallScore = liveVoiceScore !== null || liveFaceScore !== null
    ? Math.round((voiceScoreDisplay + (liveFaceScore ? faceScoreDisplay : voiceScoreDisplay)) / 2)
    : 0;

  const securityLevel = overallScore >= 85 ? 'HIGH' : overallScore >= 60 ? 'MEDIUM' : 'LOW';
  const securityColor = securityLevel === 'HIGH' ? '#00ff88' : securityLevel === 'MEDIUM' ? '#ffd700' : '#ff4444';

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(0,8,30,0.97) 0%, rgba(0,20,50,0.97) 100%)',
      border: '1px solid rgba(0,212,255,0.15)',
      borderRadius: '16px',
      padding: '20px',
      fontFamily: "'Inter', -apple-system, sans-serif",
      color: '#fff',
      minWidth: '300px',
      maxWidth: '360px',
      boxShadow: '0 0 30px rgba(0,212,255,0.08), inset 0 1px 0 rgba(255,255,255,0.05)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Corner accent */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
        background: 'linear-gradient(90deg, transparent, #00d4ff, #7b2fff, transparent)',
      }} />

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
        <div>
          <div style={{ fontSize: '11px', letterSpacing: '3px', color: '#00d4ff', textTransform: 'uppercase', fontWeight: '700' }}>
            ◈ BIOMETRIC HUD
          </div>
          <div style={{ fontSize: '18px', fontWeight: '800', background: 'linear-gradient(135deg, #fff 0%, #00d4ff 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginTop: '2px' }}>
            Security Dashboard
          </div>
        </div>
        <div style={{
          background: authStatus === 'VERIFIED' ? 'rgba(0,255,136,0.1)' : authStatus === 'REJECTED' ? 'rgba(255,68,68,0.15)' : 'rgba(0,212,255,0.08)',
          border: `1px solid ${authStatus === 'VERIFIED' ? '#00ff88' : authStatus === 'REJECTED' ? '#ff4444' : '#00d4ff'}40`,
          borderRadius: '8px',
          padding: '6px 10px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '8px', color: 'rgba(255,255,255,0.4)', letterSpacing: '1px' }}>STATUS</div>
          <div style={{ fontSize: '11px', fontWeight: '700', color: authStatus === 'VERIFIED' ? '#00ff88' : authStatus === 'REJECTED' ? '#ff4444' : '#00d4ff', fontFamily: 'monospace' }}>
            {authStatus}
          </div>
        </div>
      </div>

      {/* Score Gauges */}
      <div style={{
        display: 'flex', justifyContent: 'space-around', alignItems: 'center',
        background: 'rgba(255,255,255,0.03)', borderRadius: '10px', padding: '14px 8px',
        marginBottom: '16px', border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <ScoreGauge score={voiceScoreDisplay} label="Voice" color="#00d4ff" />
        <ScoreGauge score={faceScoreDisplay} label="Face" color="#7b2fff" />
        <ScoreGauge score={overallScore} label="Overall" color={securityColor} />
      </div>

      {/* Security Level Bar */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', letterSpacing: '1px', textTransform: 'uppercase' }}>Security Level</span>
          <span style={{ fontSize: '11px', fontWeight: '700', color: securityColor, fontFamily: 'monospace' }}>{securityLevel}</span>
        </div>
        <div style={{ height: '4px', borderRadius: '2px', background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
          <div style={{
            height: '100%',
            width: `${overallScore}%`,
            background: `linear-gradient(90deg, ${securityColor}88, ${securityColor})`,
            borderRadius: '2px',
            transition: 'width 0.6s ease',
            boxShadow: `0 0 8px ${securityColor}88`,
          }} />
        </div>
      </div>

      {/* Voice Match Threshold Slider */}
      <div style={{
        background: 'rgba(255,255,255,0.03)', borderRadius: '10px', padding: '12px 14px',
        marginBottom: '14px', border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', letterSpacing: '1px', textTransform: 'uppercase' }}>
            Voice Threshold
          </span>
          <span style={{ fontSize: '11px', color: '#00d4ff', fontFamily: 'monospace', fontWeight: '700' }}>
            {(threshold / 100).toFixed(2)}
          </span>
        </div>
        <input
          type="range" min="60" max="99" value={threshold}
          onChange={e => setThreshold(Number(e.target.value))}
          style={{ width: '100%', accentColor: '#00d4ff', cursor: 'pointer' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'rgba(255,255,255,0.25)', marginTop: '4px' }}>
          <span>0.60 (Lenient)</span>
          <span>0.99 (Strict)</span>
        </div>
      </div>

      {/* Audio Visualizer */}
      <div style={{
        background: 'rgba(255,255,255,0.03)', borderRadius: '10px', padding: '12px 14px',
        marginBottom: '14px', border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', letterSpacing: '1px', textTransform: 'uppercase' }}>
            Voiceprint Analyzer
          </span>
          <button
            onClick={() => setVoiceActive(p => !p)}
            style={{
              background: voiceActive ? 'rgba(255,68,68,0.15)' : 'rgba(0,212,255,0.1)',
              border: `1px solid ${voiceActive ? '#ff4444' : '#00d4ff'}40`,
              borderRadius: '5px',
              padding: '3px 8px',
              cursor: 'pointer',
              fontSize: '9px',
              color: voiceActive ? '#ff6b6b' : '#00d4ff',
              letterSpacing: '1px',
              textTransform: 'uppercase',
              fontWeight: '700',
            }}
          >
            {voiceActive ? '⏹ STOP' : '▶ ANALYZE'}
          </button>
        </div>
        <AudioVisualizer active={voiceActive} />
      </div>

      {/* Face Registration */}
      <div style={{
        background: 'rgba(255,255,255,0.03)', borderRadius: '10px', padding: '12px 14px',
        marginBottom: '14px', border: '1px solid rgba(123,47,255,0.2)',
      }}>
        <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '8px' }}>
          Face Recognition (LBPH)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>Mode:</span>
          <span style={{
            fontSize: '11px', fontWeight: '700', fontFamily: 'monospace',
            color: faceMode === 'lbph' ? '#7b2fff' : '#ffd700',
          }}>
            {faceMode === 'lbph' ? '🟣 LBPH (Identity Lock)' : '🟡 Detection Only'}
          </span>
        </div>
        <button
          onClick={handleFaceRegister}
          disabled={registering}
          style={{
            width: '100%',
            background: registering ? 'rgba(123,47,255,0.1)' : 'linear-gradient(135deg, rgba(123,47,255,0.2), rgba(0,212,255,0.15))',
            border: '1px solid rgba(123,47,255,0.4)',
            borderRadius: '7px',
            padding: '8px',
            cursor: registering ? 'wait' : 'pointer',
            color: '#fff',
            fontSize: '11px',
            fontWeight: '700',
            letterSpacing: '1px',
            textTransform: 'uppercase',
            transition: 'all 0.2s',
          }}
        >
          {registering ? '⏳ Capturing Face…' : '📷 Register Raj\'s Face'}
        </button>
        {regStatus && (
          <div style={{ marginTop: '8px', fontSize: '11px', color: regStatus.startsWith('✅') ? '#00ff88' : '#ff6b6b' }}>
            {regStatus}
          </div>
        )}
      </div>

      {/* Intruder Log */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', letterSpacing: '1px', textTransform: 'uppercase' }}>
            🔍 Intruder Log ({intruderEvents.length})
          </div>
          <button
            onClick={fetchLog}
            style={{
              background: 'transparent', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '5px', padding: '3px 8px', cursor: 'pointer',
              fontSize: '9px', color: 'rgba(255,255,255,0.4)', letterSpacing: '1px',
            }}
          >
            {loading ? '⟳' : '↺ REFRESH'}
          </button>
        </div>

        {intruderEvents.length === 0 ? (
          <div style={{
            textAlign: 'center', padding: '20px',
            color: 'rgba(255,255,255,0.2)', fontSize: '12px',
            border: '1px dashed rgba(255,255,255,0.06)', borderRadius: '8px',
          }}>
            ✅ No intrusion events recorded.
          </div>
        ) : (
          <div style={{ maxHeight: '200px', overflowY: 'auto', scrollbarWidth: 'thin' }}>
            {intruderEvents.map((ev, i) => (
              <IntruderRow key={ev.filename} event={ev} index={i} />
            ))}
          </div>
        )}

        {lastAuthTime && (
          <div style={{ marginTop: '10px', fontSize: '10px', color: 'rgba(255,255,255,0.3)', textAlign: 'center' }}>
            Last auth event: {lastAuthTime}
          </div>
        )}
      </div>
    </div>
  );
}

export default BiometricsDashboard;
