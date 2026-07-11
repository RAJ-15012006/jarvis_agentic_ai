import React, { useState, useEffect, useCallback, useRef } from 'react';

// ─── Mini Contribution Graph ────────────────────────────────────────────────
function ContribGraph({ weeks = 20 }) {
  // Generate mock graph data (real data from GitHub API would replace this)
  const cells = [];
  for (let w = 0; w < weeks; w++) {
    const col = [];
    for (let d = 0; d < 7; d++) {
      const val = Math.random();
      col.push(val > 0.6 ? (val > 0.85 ? 3 : val > 0.75 ? 2 : 1) : 0);
    }
    cells.push(col);
  }

  const colors = [
    'rgba(255,255,255,0.06)',
    '#0e4429', '#006d32', '#26a641', '#39d353'
  ];

  return (
    <div style={{ display: 'flex', gap: '2px' }}>
      {cells.map((week, wi) => (
        <div key={wi} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {week.map((level, di) => (
            <div key={di} style={{
              width: 8, height: 8, borderRadius: '2px',
              background: colors[level],
              transition: 'background 0.3s',
            }} />
          ))}
        </div>
      ))}
    </div>
  );
}

// ─── Stat Card ──────────────────────────────────────────────────────────────
function StatCard({ icon, label, value, color = '#00d4ff' }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)',
      border: `1px solid ${color}22`,
      borderRadius: '8px',
      padding: '8px 10px',
      textAlign: 'center',
      flex: 1,
    }}>
      <div style={{ fontSize: '16px', marginBottom: '2px' }}>{icon}</div>
      <div style={{ fontSize: '14px', fontWeight: '800', color, fontFamily: 'monospace' }}>{value}</div>
      <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.35)', letterSpacing: '1px', textTransform: 'uppercase' }}>
        {label}
      </div>
    </div>
  );
}

// ─── Main GitHub Stats Widget ───────────────────────────────────────────────
export function GitHubStatsWidget({ socket }) {
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(false);
  const [gitInput, setGitInput] = useState('');
  const [lastPush, setLastPush] = useState(null);
  const GITHUB_COLOR = '#6e40c9';

  // Parse stats text from backend
  const parseStats = (text) => {
    if (!text) return null;
    const extract = (label) => {
      const match = text.match(new RegExp(`${label}:\\s*(\\d+)`));
      return match ? match[1] : '—';
    };
    const langMatch = text.match(/Top Language:\s*(\w+)/);
    return {
      repos: extract('Public Repos'),
      stars: extract('Total Stars'),
      forks: extract('Total Forks'),
      followers: extract('Followers'),
      lang: langMatch ? langMatch[1] : '—',
    };
  };

  // Parse activity lines
  const parseActivity = (text) => {
    if (!text) return [];
    return text.split('\n')
      .filter(l => l.trim().startsWith('•'))
      .map(l => l.replace('•', '').trim())
      .slice(0, 5);
  };

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/github-stats');
      const data = await res.json();
      if (data.success) {
        setStats(parseStats(data.stats));
        setActivity(parseActivity(data.activity));
      }
    } catch {
      // Silent fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const timer = setInterval(fetchStats, 120000); // refresh every 2 min
    return () => clearInterval(timer);
  }, [fetchStats]);

  const handleGitCommand = async (e) => {
    e.preventDefault();
    if (!socket || !gitInput.trim()) return;
    const cmd = gitInput.trim().toLowerCase();
    let fullCmd = '';
    if (cmd === 'push') fullCmd = 'git push my changes';
    else if (cmd === 'pull') fullCmd = 'git pull';
    else if (cmd === 'status') fullCmd = 'git status';
    else fullCmd = `git ${cmd}`;
    socket.emit('process_command', { command: fullCmd, audio: '' });
    setLastPush(new Date().toLocaleTimeString());
    setGitInput('');
    setTimeout(fetchStats, 3000);
  };

  const parsedStats = stats;

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(0,0,0,0.95), rgba(10,6,25,0.98))',
      border: `1px solid ${GITHUB_COLOR}33`,
      borderRadius: '14px',
      padding: '14px',
      fontFamily: "'Inter', sans-serif",
      color: '#fff',
      boxShadow: `0 0 20px ${GITHUB_COLOR}15`,
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Top accent */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
        background: `linear-gradient(90deg, transparent, ${GITHUB_COLOR}, transparent)`,
      }} />

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '16px' }}>🐙</span>
          <span style={{ fontSize: '10px', fontWeight: '700', letterSpacing: '2px', color: GITHUB_COLOR, textTransform: 'uppercase' }}>
            GITHUB STATS
          </span>
        </div>
        <button onClick={fetchStats} style={{
          background: 'transparent', border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '5px', padding: '2px 7px', cursor: 'pointer',
          fontSize: '9px', color: 'rgba(255,255,255,0.4)', letterSpacing: '1px',
        }}>
          {loading ? '⟳' : '↺ SYNC'}
        </button>
      </div>

      {/* Stat Cards */}
      {parsedStats ? (
        <div style={{ display: 'flex', gap: '6px', marginBottom: '12px' }}>
          <StatCard icon="🗂️" label="Repos" value={parsedStats.repos} color="#00d4ff" />
          <StatCard icon="⭐" label="Stars" value={parsedStats.stars} color="#ffd700" />
          <StatCard icon="👥" label="Followers" value={parsedStats.followers} color={GITHUB_COLOR} />
        </div>
      ) : (
        <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)', textAlign: 'center', padding: '8px' }}>
          {loading ? 'Loading stats...' : 'Say "show my GitHub stats"'}
        </div>
      )}

      {/* Contribution Graph */}
      <div style={{
        background: 'rgba(255,255,255,0.02)', borderRadius: '8px',
        padding: '10px', marginBottom: '10px', overflowX: 'auto',
      }}>
        <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.3)', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '6px' }}>
          Contribution Activity
        </div>
        <ContribGraph weeks={20} />
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
          <span style={{ fontSize: '8px', color: 'rgba(255,255,255,0.2)' }}>Less</span>
          {['rgba(255,255,255,0.06)', '#0e4429', '#26a641', '#39d353'].map((c, i) => (
            <div key={i} style={{ width: 8, height: 8, borderRadius: '2px', background: c }} />
          ))}
          <span style={{ fontSize: '8px', color: 'rgba(255,255,255,0.2)' }}>More</span>
        </div>
      </div>

      {/* Recent Activity */}
      {activity.length > 0 && (
        <div style={{ marginBottom: '10px' }}>
          <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.3)', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '6px' }}>
            Recent Pushes
          </div>
          {activity.slice(0, 3).map((item, i) => (
            <div key={i} style={{
              fontSize: '10px', color: 'rgba(255,255,255,0.55)',
              padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
              fontFamily: 'monospace',
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>
              {item}
            </div>
          ))}
        </div>
      )}

      {/* Voice Git Commands */}
      <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.3)', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '6px' }}>
        Quick Git
      </div>
      <form onSubmit={handleGitCommand} style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
        <input
          value={gitInput}
          onChange={e => setGitInput(e.target.value)}
          placeholder="push / pull / status"
          style={{
            flex: 1, background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '6px', padding: '5px 8px',
            color: '#fff', fontSize: '11px', outline: 'none', fontFamily: 'monospace',
          }}
        />
        <button type="submit" style={{
          background: GITHUB_COLOR, border: 'none', borderRadius: '6px',
          padding: '5px 10px', cursor: 'pointer', color: '#fff',
          fontSize: '11px', fontWeight: '700',
        }}>▶</button>
      </form>

      {/* Quick action buttons */}
      <div style={{ display: 'flex', gap: '6px' }}>
        {['push', 'pull', 'status'].map(cmd => (
          <button key={cmd} onClick={() => { setGitInput(cmd); }}
            style={{
              flex: 1, background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '5px', padding: '4px 0',
              cursor: 'pointer', color: 'rgba(255,255,255,0.5)',
              fontSize: '9px', fontWeight: '700',
              letterSpacing: '1px', textTransform: 'uppercase',
            }}
          >
            {cmd}
          </button>
        ))}
      </div>

      {lastPush && (
        <div style={{ marginTop: '6px', fontSize: '9px', color: 'rgba(255,255,255,0.25)', textAlign: 'center' }}>
          Last git command: {lastPush}
        </div>
      )}
    </div>
  );
}

export default GitHubStatsWidget;
