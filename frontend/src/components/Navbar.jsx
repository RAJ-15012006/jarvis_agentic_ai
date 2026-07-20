import React, { useState, useEffect } from 'react';

export const Navbar = () => {
  const [activeModal, setActiveModal] = useState(null);
  const [listenerActive, setListenerActive] = useState(false);
  const [restartingListener, setRestartingListener] = useState(false);

  const checkListenerStatus = async () => {
    try {
      const baseUrl = window.location.origin.includes('localhost') ? 'http://localhost:8000' : (window.location.origin.includes('jarvis.weblog') ? 'http://jarvis.weblog:8000' : window.location.origin);
      const res = await fetch(`${baseUrl}/api/listener-status`);
      const data = await res.json();
      setListenerActive(data.active);
    } catch (e) {
      setListenerActive(false);
    }
  };

  const restartListener = async () => {
    setRestartingListener(true);
    try {
      const baseUrl = window.location.origin.includes('localhost') ? 'http://localhost:8000' : (window.location.origin.includes('jarvis.weblog') ? 'http://jarvis.weblog:8000' : window.location.origin);
      await fetch(`${baseUrl}/api/listener-restart`, { method: 'POST' });
      await checkListenerStatus();
    } catch (e) {
      console.error(e);
    } finally {
      setRestartingListener(false);
    }
  };

  useEffect(() => {
    checkListenerStatus();
    const interval = setInterval(checkListenerStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const resetVoice = () => {
    localStorage.removeItem('jarvis_voice');
    window.location.reload();
  };

  return (
    <>
      <nav className="fixed top-0 left-0 w-full h-16 flex items-center justify-between px-8 z-50 pointer-events-auto border-b border-jarvis-cyan/20 bg-black/40 backdrop-blur-sm">
        <div className="flex items-center space-x-4">
          <div className="flex space-x-1">
            <div className="w-2 h-6 bg-jarvis-cyan animate-pulse"></div>
            <div className="w-2 h-6 bg-jarvis-cyan/50"></div>
            <div className="w-2 h-6 bg-jarvis-cyan/20"></div>
          </div>
          <h1 className="font-orbitron text-2xl tracking-[0.2em] font-bold text-jarvis-cyan shadow-jarvis-cyan drop-shadow-[0_0_10px_rgba(0,255,209,0.8)]">
            J.A.R.V.I.S.
          </h1>
        </div>
        <div className="hidden md:flex items-center space-x-8 font-rajdhani font-semibold tracking-wider text-sm text-jarvis-cyan/70">
          <button onClick={() => setActiveModal(null)} className="hover:text-jarvis-cyan hover:drop-shadow-[0_0_8px_rgba(0,255,209,0.8)] transition-all uppercase focus:outline-none">HOME</button>
          <button onClick={() => setActiveModal(null)} className="hover:text-jarvis-cyan hover:drop-shadow-[0_0_8px_rgba(0,255,209,0.8)] transition-all uppercase focus:outline-none">DASHBOARD</button>
          <button onClick={() => setActiveModal('settings')} className="hover:text-jarvis-cyan hover:drop-shadow-[0_0_8px_rgba(0,255,209,0.8)] transition-all uppercase focus:outline-none">SETTINGS</button>
          <button onClick={() => setActiveModal('about')} className="hover:text-jarvis-cyan hover:drop-shadow-[0_0_8px_rgba(0,255,209,0.8)] transition-all uppercase focus:outline-none">ABOUT</button>
        </div>
      </nav>

      {/* Modals */}
      {activeModal === 'settings' && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-md pointer-events-auto">
          <div className="bg-black/90 border border-jarvis-cyan/40 p-8 rounded-lg shadow-[0_0_30px_rgba(0,255,209,0.2)] max-w-lg w-full relative">
            <button onClick={() => setActiveModal(null)} className="absolute top-4 right-4 text-jarvis-cyan hover:text-white font-orbitron text-xl">X</button>
            <h2 className="text-2xl font-orbitron tracking-[0.2em] text-jarvis-cyan mb-6">SYSTEM SETTINGS</h2>
            <div className="space-y-6 text-jarvis-cyan font-rajdhani text-lg">
              <div className="flex justify-between items-center border-b border-jarvis-cyan/20 pb-4">
                <span>Vocal Core Configuration</span>
                <button onClick={resetVoice} className="px-4 py-1 border border-jarvis-cyan hover:bg-jarvis-cyan hover:text-black transition-all rounded text-sm">RECONFIGURE</button>
              </div>
              <div className="flex justify-between items-center border-b border-jarvis-cyan/20 pb-4">
                <span>UI Hologram Mode</span>
                <span className="text-green-400">ACTIVE</span>
              </div>
              <div className="flex justify-between items-center border-b border-jarvis-cyan/20 pb-4">
                <span>
                  Global Voice Listener<br />
                  <span className="text-[10px] text-jarvis-cyan/50">(For listening in other tabs)</span>
                </span>
                <div className="flex items-center gap-3">
                  <span className={listenerActive ? "text-green-400 font-bold" : "text-amber-500 font-bold"}>
                    {listenerActive ? "● ACTIVE" : "● INACTIVE"}
                  </span>
                  <button
                    onClick={restartListener}
                    disabled={restartingListener}
                    className="px-3 py-1 border border-jarvis-cyan/40 hover:border-jarvis-cyan hover:bg-jarvis-cyan hover:text-black transition-all rounded text-xs"
                  >
                    {restartingListener ? "RESTARTING..." : "RESTART"}
                  </button>
                </div>
              </div>
              <div className="flex justify-between items-center pb-2">
                <span>Socket Connection</span>
                <span className="text-green-400 animate-pulse">SECURE</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeModal === 'about' && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-md pointer-events-auto">
          <div className="bg-black/90 border border-jarvis-cyan/40 p-8 rounded-lg shadow-[0_0_30px_rgba(0,255,209,0.2)] max-w-md w-full relative text-center">
            <button onClick={() => setActiveModal(null)} className="absolute top-4 right-4 text-jarvis-cyan hover:text-white font-orbitron text-xl">X</button>
            <h2 className="text-2xl font-orbitron tracking-[0.2em] text-jarvis-cyan mb-2">J.A.R.V.I.S. OS</h2>
            <p className="text-jarvis-cyan/70 font-rajdhani mb-6">Version 1.0.0 (Build 8492)</p>
            <div className="space-y-2 text-left bg-jarvis-cyan/5 p-4 rounded border border-jarvis-cyan/10 font-mono text-sm text-jarvis-cyan/80">
              <p>{">"} USER IDENTIFIED: RAJ</p>
              <p>{">"} CORE: LLAMA-3.3-70B</p>
              <p>{">"} MODULES: WEB, VOICE, AUTOMATION</p>
              <p>{">"} UI: REACT THREE FIBER (3D)</p>
              <p>{">"} STATUS: OPTIMAL</p>
            </div>
            <p className="mt-6 text-xs text-jarvis-cyan/50 font-rajdhani">Designed strictly for authorized personnel only.</p>
          </div>
        </div>
      )}
    </>
  );
};
