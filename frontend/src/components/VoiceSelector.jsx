import React, { useEffect } from 'react';

export const VoiceSelector = ({ onComplete }) => {
  useEffect(() => {
    const saved = localStorage.getItem('jarvis_voice');
    if (saved) {
      // Sync with backend on startup
      const baseUrl = window.location.origin.includes('localhost') ? 'http://localhost:8000' : window.location.origin;
      fetch(`${baseUrl}/api/voice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gender: saved })
      }).catch(() => {});
      
      // Commented out to ensure we always ask the user for male or female voice
      // onComplete();
    }
  }, [onComplete]);

  const selectVoice = async (gender) => {
    localStorage.setItem('jarvis_voice', gender);
    const baseUrl = window.location.origin.includes('localhost') ? 'http://localhost:8000' : window.location.origin;
    try {
      await fetch(`${baseUrl}/api/voice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gender })
      });
    } catch { /* voice sync is best-effort */ }
    onComplete();
  };

  return (
    <div className="w-screen h-screen flex items-center justify-center bg-black relative overflow-hidden">
      <div className="scanlines z-0"></div>
      <div className="bg-black/80 border border-jarvis-cyan/30 p-8 rounded-lg shadow-[0_0_40px_rgba(0,255,209,0.15)] max-w-lg w-full text-center relative z-10">
        <h2 className="text-2xl font-orbitron tracking-[0.2em] text-jarvis-cyan mb-8">INITIALIZE VOCAL CORE</h2>
        <div className="flex gap-6 justify-center">
          <button 
            onClick={() => selectVoice('male')}
            className="flex-1 py-4 border border-jarvis-cyan text-jarvis-cyan hover:bg-jarvis-cyan hover:text-black font-rajdhani text-xl font-bold tracking-widest transition-all uppercase shadow-[0_0_15px_rgba(0,255,209,0.3)] hover:shadow-[0_0_25px_rgba(0,255,209,0.6)]"
          >
            MALE VOICE
          </button>
          <button 
            onClick={() => selectVoice('female')}
            className="flex-1 py-4 border border-[#f472b6] text-[#f472b6] hover:bg-[#f472b6] hover:text-black font-rajdhani text-xl font-bold tracking-widest transition-all uppercase shadow-[0_0_15px_rgba(244,114,182,0.3)] hover:shadow-[0_0_25px_rgba(244,114,182,0.6)]"
          >
            FEMALE VOICE
          </button>
        </div>
      </div>
    </div>
  );
};
