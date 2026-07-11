import React, { useState, useEffect, useRef, useCallback } from 'react';

// ─── Album Art Placeholder ──────────────────────────────────────────────────
function AlbumArtPulse({ isPlaying, color = '#1db954' }) {
  return (
    <div style={{ position: 'relative', width: 56, height: 56, flexShrink: 0 }}>
      {/* Outer pulse rings */}
      {isPlaying && [0, 1, 2].map(i => (
        <div key={i} style={{
          position: 'absolute', inset: -(i * 6), borderRadius: '50%',
          border: `1px solid ${color}${['55', '33', '18'][i]}`,
          animation: `pulse-ring 1.5s ease-in-out infinite`,
          animationDelay: `${i * 0.3}s`,
        }} />
      ))}
      <div style={{
        width: '100%', height: '100%', borderRadius: '50%',
        background: `linear-gradient(135deg, #1a1a2e, #16213e)`,
        border: `2px solid ${color}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '22px', position: 'relative', zIndex: 1,
      }}>
        🎵
      </div>
    </div>
  );
}

// ─── Progress Bar ──────────────────────────────────────────────────────────
function ProgressBar({ progress = 0, color = '#1db954' }) {
  return (
    <div style={{ height: '3px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
      <div style={{
        height: '100%', width: `${progress}%`,
        background: `linear-gradient(90deg, ${color}, ${color}cc)`,
        borderRadius: '2px',
        transition: 'width 1s linear',
        boxShadow: `0 0 6px ${color}88`,
      }} />
    </div>
  );
}

// ─── Mini Equalizer Bars ──────────────────────────────────────────────────
function EqualizerBars({ isPlaying, color = '#1db954' }) {
  return (
    <div style={{ display: 'flex', gap: '2px', alignItems: 'flex-end', height: '16px' }}>
      {[0.6, 1, 0.7, 0.9, 0.5].map((h, i) => (
        <div key={i} style={{
          width: '3px',
          background: color,
          borderRadius: '2px',
          height: isPlaying ? `${h * 16}px` : '4px',
          animation: isPlaying ? `eq-bar 0.8s ease-in-out infinite alternate` : 'none',
          animationDelay: `${i * 0.12}s`,
          transition: 'height 0.2s ease',
          opacity: 0.85,
        }} />
      ))}
    </div>
  );
}

// ─── Main Spotify Widget ──────────────────────────────────────────────────
export function SpotifyWidget({ socket }) {
  const [track, setTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [volume, setVolume] = useState(70);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState(null);
  const progressRef = useRef(null);
  const SPOTIFY_GREEN = '#1db954';

  const fetchNowPlaying = useCallback(async () => {
    try {
      const res = await fetch('/api/spotify-now-playing');
      const data = await res.json();
      if (data.success && data.result && !data.result.includes('Nothing')) {
        // Parse the text response
        const match = data.result.match(/Now playing: '(.+)' by (.+)\n\s+Album: (.+) \| Progress: (\d+)%/);
        if (match) {
          setTrack({ name: match[1], artist: match[2], album: match[3] });
          setProgress(parseInt(match[4]));
          setIsPlaying(data.result.includes('▶'));
        }
      } else {
        setIsPlaying(false);
      }
      setError(null);
    } catch {
      setError('Spotify not connected');
    }
  }, []);

  useEffect(() => {
    fetchNowPlaying();
    const timer = setInterval(fetchNowPlaying, 10000);
    return () => clearInterval(timer);
  }, [fetchNowPlaying]);

  // Listen for Spotify updates via WebSocket
  useEffect(() => {
    if (!socket) return;
    const handler = () => setTimeout(fetchNowPlaying, 1500);
    socket.on('spotify_update', handler);
    return () => socket.off('spotify_update', handler);
  }, [socket, fetchNowPlaying]);

  const sendSpotifyCommand = async (cmd) => {
    if (!socket) return;
    setLoading(true);
    socket.emit('process_command', { command: cmd, audio: '' });
    setTimeout(() => {
      setLoading(false);
      fetchNowPlaying();
    }, 1200);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    sendSpotifyCommand(`play ${searchQuery} on spotify`);
    setSearchQuery('');
  };

  const btnStyle = (active = false) => ({
    background: active ? `${SPOTIFY_GREEN}22` : 'transparent',
    border: `1px solid ${active ? SPOTIFY_GREEN : 'rgba(255,255,255,0.1)'}`,
    borderRadius: '50%',
    width: 32, height: 32,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    cursor: loading ? 'wait' : 'pointer',
    color: active ? SPOTIFY_GREEN : 'rgba(255,255,255,0.7)',
    fontSize: '14px',
    transition: 'all 0.15s',
  });

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(0,0,0,0.95), rgba(18,18,18,0.98))',
      border: `1px solid ${SPOTIFY_GREEN}33`,
      borderRadius: '14px',
      padding: '14px',
      fontFamily: "'Inter', sans-serif",
      color: '#fff',
      boxShadow: `0 0 20px ${SPOTIFY_GREEN}15`,
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Top accent */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
        background: `linear-gradient(90deg, transparent, ${SPOTIFY_GREEN}, transparent)`,
      }} />

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '16px' }}>🎵</span>
          <span style={{ fontSize: '10px', fontWeight: '700', letterSpacing: '2px', color: SPOTIFY_GREEN, textTransform: 'uppercase' }}>
            SPOTIFY
          </span>
        </div>
        <EqualizerBars isPlaying={isPlaying} color={SPOTIFY_GREEN} />
      </div>

      {/* Now Playing */}
      {error ? (
        <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)', textAlign: 'center', padding: '8px' }}>
          {error} — Say "play [song] on Spotify"
        </div>
      ) : track ? (
        <div style={{ marginBottom: '12px' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '10px' }}>
            <AlbumArtPulse isPlaying={isPlaying} color={SPOTIFY_GREEN} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '13px', fontWeight: '700', color: '#fff', 
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {track.name}
              </div>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginTop: '2px' }}>
                {track.artist}
              </div>
              <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.3)', marginTop: '1px' }}>
                {track.album}
              </div>
            </div>
          </div>
          <ProgressBar progress={progress} color={SPOTIFY_GREEN} />
        </div>
      ) : (
        <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)', textAlign: 'center', padding: '8px 0' }}>
          Nothing playing — say "play [song name]"
        </div>
      )}

      {/* Controls */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', alignItems: 'center', marginBottom: '10px' }}>
        <button onClick={() => sendSpotifyCommand('previous song spotify')} style={btnStyle()}>⏮</button>
        <button 
          onClick={() => sendSpotifyCommand(isPlaying ? 'pause spotify' : 'resume spotify')}
          style={{
            ...btnStyle(true),
            width: 40, height: 40,
            fontSize: '16px',
            background: SPOTIFY_GREEN,
            color: '#000',
            fontWeight: '700',
          }}
        >
          {isPlaying ? '⏸' : '▶'}
        </button>
        <button onClick={() => sendSpotifyCommand('next song spotify')} style={btnStyle()}>⏭</button>
        <button onClick={() => sendSpotifyCommand('shuffle on spotify')} style={btnStyle()}>🔀</button>
      </div>

      {/* Volume */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
        <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)' }}>🔉</span>
        <input
          type="range" min="0" max="100" value={volume}
          onChange={e => {
            setVolume(Number(e.target.value));
            sendSpotifyCommand(`spotify volume to ${e.target.value}`);
          }}
          style={{ flex: 1, accentColor: SPOTIFY_GREEN, cursor: 'pointer' }}
        />
        <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', fontFamily: 'monospace' }}>{volume}%</span>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '6px' }}>
        <input
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="Search a song..."
          style={{
            flex: 1, background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '6px', padding: '5px 8px',
            color: '#fff', fontSize: '11px', outline: 'none',
          }}
        />
        <button type="submit" style={{
          background: SPOTIFY_GREEN, border: 'none', borderRadius: '6px',
          padding: '5px 10px', cursor: 'pointer', color: '#000',
          fontSize: '11px', fontWeight: '700',
        }}>▶</button>
      </form>

      <style>{`
        @keyframes eq-bar {
          from { height: 4px; }
          to { height: 16px; }
        }
        @keyframes pulse-ring {
          from { transform: scale(1); opacity: 0.6; }
          to { transform: scale(1.1); opacity: 0; }
        }
      `}</style>
    </div>
  );
}

export default SpotifyWidget;
