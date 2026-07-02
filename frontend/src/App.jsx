import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { Navbar } from './components/Navbar';
import { Globe3D } from './components/Globe3D';
import { SystemStatus } from './components/SystemStatus';
import { ActivityMonitor } from './components/ActivityMonitor';
import { SystemInfo } from './components/SystemInfo';
import { SystemLog } from './components/SystemLog';
import { GreetingCard } from './components/GreetingCard';
import { IronManTopLeft } from './components/IronManTopLeft';
import { NeuralCore3D } from './components/NeuralCore3D';
import { VoiceSelector } from './components/VoiceSelector';
import { DocumentAnalysis } from './components/DocumentAnalysis';
import { GenderDetection } from './components/GenderDetection';
import jarvisAvatar from './assets/jarvis_avatar.jpg';

const socket = io(window.location.origin.includes('localhost') ? 'http://localhost:8000' : window.location.origin, { autoConnect: false, auth: { token: 'jarvis-local-secret' } });

// Secret voice passphrase — only Raj knows this
const VOICE_PASSPHRASE = 'avneet is mine';

function PasswordGate({ onUnlock }) {
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [shake, setShake] = useState(false);
  const [stage, setStage] = useState('password'); // 'password'|'fingerprint'|'voice'|'denied'|'locked'
  const [voiceStatus, setVoiceStatus] = useState('Press the button and say the passphrase');
  const [listening, setListening] = useState(false);
  const [showTypeFallback, setShowTypeFallback] = useState(false);
  const [typedPassphrase, setTypedPassphrase] = useState('');
  const voiceAttempts = useRef(0);

  // Fingerprint states
  const [fpProgress, setFpProgress] = useState(0);
  const [fpStatus, setFpStatus] = useState('Hold to scan biometric data');
  const [isScanning, setIsScanning] = useState(false);
  const scanIntervalRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (input !== 'avneet') {
      setError('Wrong password. Access denied.');
      setShake(true);
      setInput('');
      setTimeout(() => setShake(false), 500);
      return;
    }
    setStage('fingerprint');
    setError('');
  };

  const triggerTouchID = async () => {
    if (!window.PublicKeyCredential) {
      setFpStatus('Touch ID not supported on this browser.');
      return;
    }
    
    try {
      // Check if platform authenticator is available (Touch ID/Windows Hello)
      const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
      if (!available) {
        setFpStatus('No Touch ID sensor found on this device.');
        return;
      }

      setIsScanning(true);
      setFpStatus('Waiting for Touch ID...');
      
      const challenge = new Uint8Array(32);
      window.crypto.getRandomValues(challenge);
      
      const userID = new Uint8Array(16);
      window.crypto.getRandomValues(userID);

      // Trigger the native OS biometric prompt
      await navigator.credentials.create({
        publicKey: {
          challenge: challenge,
          rp: { name: "JARVIS OS", id: window.location.hostname },
          user: { id: userID, name: "raj@jarvis", displayName: "Raj" },
          pubKeyCredParams: [{ alg: -7, type: "public-key" }, { alg: -257, type: "public-key" }],
          authenticatorSelection: { authenticatorAttachment: "platform", userVerification: "required" },
          timeout: 60000,
          attestation: "none"
        }
      });
      
      // If we reach here, biometric auth succeeded!
      setFpProgress(100);
      setFpStatus('Touch ID Verified - Granted');
      setTimeout(() => setStage('voice'), 800);
    } catch (err) {
      console.error(err);
      setIsScanning(false);
      setFpStatus('Touch ID failed or cancelled.');
    }
  };

  const startVoiceAuth = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { setVoiceStatus('Speech not supported. Use Chrome.'); return; }

    const recognition = new SR();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 5;

    setListening(true);
    setVoiceStatus('Listening... say the passphrase now');
    recognition.start();

    recognition.onresult = (event) => {
      let heard = '';
      for (let i = 0; i < event.results[0].length; i++) {
        heard = event.results[0][i].transcript.toLowerCase().trim();
        const words    = VOICE_PASSPHRASE.split(' ');
        const heardW   = heard.split(' ');
        const matches  = words.filter(w => heardW.includes(w)).length;
        if (matches >= words.length - 1) {
          setListening(false);
          setVoiceStatus('Passphrase verified!');
          setTimeout(() => onUnlock(), 800);
          return;
        }
      }
      voiceAttempts.current += 1;
      setListening(false);
      if (voiceAttempts.current >= 3) {
        setStage('locked');
        setError('Voice passphrase failed 3 times. System locked.');
      } else {
        setVoiceStatus(`Wrong passphrase. ${3 - voiceAttempts.current} attempt(s) left. Heard: "${heard}"`);
      }
    };

    recognition.onerror = (e) => {
      setListening(false);
      setVoiceStatus(`Mic error: ${e.error}. Try again.`);
    };

    recognition.onend = () => setListening(false);
  };

  return (
    <div className="w-screen h-screen flex items-center justify-center bg-black">
      <div
        className={`flex flex-col items-center gap-6 p-10 border border-jarvis-cyan/40 rounded-xl bg-black/80 ${
          shake ? 'animate-[shake_0.4s_ease]' : ''
        }`}
        style={{ boxShadow: '0 0 40px 4px #00ffd133', minWidth: 340 }}
      >
        <img src={jarvisAvatar} alt="JARVIS" className="w-20 h-20 rounded-full border-2 border-jarvis-cyan/60 object-cover" />
        <p className="font-orbitron text-jarvis-cyan text-lg tracking-widest">JARVIS ACCESS</p>

        {/* STAGE 1 — Password */}
        {stage === 'password' && (
          <form onSubmit={handleSubmit} className="flex flex-col items-center gap-3 w-full">
            <p className="text-jarvis-cyan/50 font-mono text-xs tracking-widest">STEP 1 OF 3 — PASSWORD</p>
            <input
              autoFocus
              type="password"
              value={input}
              onChange={(e) => { setInput(e.target.value); setError(''); }}
              placeholder="Enter password"
              className="w-full bg-transparent border border-jarvis-cyan/40 rounded-lg px-4 py-2 text-jarvis-cyan font-mono text-sm outline-none placeholder-jarvis-cyan/30 text-center tracking-widest"
            />
            {error && <p className="text-red-400 font-mono text-xs">{error}</p>}
            <button type="submit" className="w-full border border-jarvis-cyan/50 text-jarvis-cyan font-orbitron text-xs py-2 rounded-lg hover:bg-jarvis-cyan/10 transition-all tracking-widest">
              AUTHENTICATE
            </button>
          </form>
        )}

        {/* STAGE 2 — Fingerprint */}
        {stage === 'fingerprint' && (
          <div className="flex flex-col items-center gap-4 w-full">
            <p className="text-jarvis-cyan/50 font-mono text-xs tracking-widest">STEP 2 OF 3 — BIOMETRICS</p>
            <div 
              className="relative w-32 h-32 rounded-full border-2 border-jarvis-cyan/30 flex items-center justify-center cursor-pointer overflow-hidden transition-all duration-300 select-none hover:bg-jarvis-cyan/10"
              style={{
                boxShadow: isScanning ? '0 0 30px 5px #00ffd166, inset 0 0 20px 2px #00ffd133' : '0 0 10px 1px #00ffd122',
                borderColor: isScanning ? '#00ffd1' : 'rgba(0, 255, 209, 0.3)'
              }}
              onClick={triggerTouchID}
            >
              {/* SVG Fingerprint Icon */}
              <svg className={`w-16 h-16 transition-all duration-300 ${isScanning ? 'text-jarvis-cyan scale-110 drop-shadow-[0_0_12px_#00ffd1]' : 'text-jarvis-cyan/40'}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
                <path d="M12 6c-3.31 0-6 2.69-6 6 0 1.66.67 3.16 1.76 4.24l1.41-1.41C8.44 14.07 8 13.09 8 12c0-2.21 1.79-4 4-4s4 1.79 4 4c0 1.09-.44 2.07-1.17 2.83l1.41 1.41C17.33 15.16 18 13.66 18 12c0-3.31-2.69-6-6-6z" />
                <path d="M12 10c-1.1 0-2 .9-2 2 0 .55.22 1.05.59 1.41l1.41-1.41c-.13-.13-.2-.3-.2-.59 0-.55.45-1 1-1s1 .45 1 1c0 .28-.11.53-.29.71l1.41 1.41C14.78 13.05 15 12.55 15 12c0-1.1-.9-2-2-2z" />
              </svg>
              
              {/* Scanning Laser */}
              {isScanning && (
                <div 
                  className="absolute left-0 w-full h-[2px] bg-jarvis-cyan shadow-[0_0_8px_2px_#00ffd1] opacity-80"
                  style={{
                    top: `${fpProgress}%`,
                    transition: 'top 0.05s linear'
                  }}
                />
              )}
              
              {/* Fill background progress */}
              <div 
                className="absolute bottom-0 left-0 w-full bg-jarvis-cyan/20 transition-all duration-75"
                style={{ height: `${fpProgress}%` }}
              />
            </div>
            
            <p className={`font-mono text-xs text-center h-4 ${isScanning ? 'text-jarvis-cyan animate-pulse' : 'text-jarvis-cyan/50'}`}>
              {fpStatus}
            </p>
            <div className="w-full h-1 bg-jarvis-cyan/20 rounded-full mt-2">
              <div 
                className="h-full bg-jarvis-cyan rounded-full transition-all duration-75 shadow-[0_0_5px_#00ffd1]" 
                style={{ width: `${fpProgress}%` }}
              />
            </div>
            <p className="text-[10px] text-jarvis-cyan/40 font-mono tracking-widest">{fpProgress}% COMPLETE</p>
          </div>
        )}

        {/* STAGE 3 — Voice Passphrase */}
        {stage === 'voice' && (
          <div className="flex flex-col items-center gap-4 w-full">
            <p className="text-jarvis-cyan/50 font-mono text-xs tracking-widest">STEP 3 OF 3 — VOICE PASSPHRASE</p>
            {showTypeFallback ? (
              <>
                <p className="text-jarvis-cyan/70 font-mono text-xs text-center">Type the secret passphrase</p>
                <input
                  autoFocus
                  type="text"
                  value={typedPassphrase}
                  onChange={(e) => {
                    setTypedPassphrase(e.target.value);
                    if (e.target.value.toLowerCase().trim() === VOICE_PASSPHRASE) {
                      setVoiceStatus('Passphrase verified!');
                      setTimeout(() => onUnlock(), 800);
                    }
                  }}
                  placeholder="Enter passphrase"
                  className="w-full bg-transparent border border-jarvis-cyan/40 rounded-lg px-4 py-2 text-jarvis-cyan font-mono text-sm outline-none placeholder-jarvis-cyan/30 text-center tracking-widest"
                />
                <button
                  type="button"
                  onClick={() => setShowTypeFallback(false)}
                  className="text-jarvis-cyan/50 hover:text-jarvis-cyan font-mono text-[10px] underline mt-2"
                >
                  Use Voice Authentication
                </button>
              </>
            ) : (
              <>
                <p className="text-jarvis-cyan/70 font-mono text-xs text-center">Say your secret passphrase</p>
                <button
                  onClick={startVoiceAuth}
                  disabled={listening}
                  className={`w-full font-orbitron text-xs py-3 rounded-lg border transition-all tracking-widest ${
                    listening
                      ? 'border-green-400/50 text-green-400 bg-green-400/10 animate-pulse'
                      : 'border-jarvis-cyan/50 text-jarvis-cyan hover:bg-jarvis-cyan/10'
                  }`}
                >
                  {listening ? 'LISTENING...' : 'SPEAK PASSPHRASE'}
                </button>
                <p className="text-jarvis-cyan/60 font-mono text-xs text-center">{voiceStatus}</p>
                <button
                  type="button"
                  onClick={() => setShowTypeFallback(true)}
                  className="text-jarvis-cyan/50 hover:text-jarvis-cyan font-mono text-[10px] underline mt-2"
                >
                  Can't use mic? Type passphrase
                </button>
              </>
            )}
          </div>
        )}

        {/* DENIED */}
        {stage === 'denied' && (
          <div className="flex flex-col items-center gap-3">
            <p className="text-red-400 font-mono text-sm text-center">{error}</p>
            <button
              onClick={() => { setStage('password'); setError(''); setInput(''); voiceAttempts.current = 0; }}
              className="border border-red-400/50 text-red-400 font-orbitron text-xs py-2 px-4 rounded-lg hover:bg-red-400/10 transition-all"
            >
              TRY AGAIN
            </button>
          </div>
        )}

        {/* LOCKED */}
        {stage === 'locked' && (
          <div className="flex flex-col items-center gap-3">
            <p className="text-red-500 font-orbitron text-sm text-center tracking-widest">SYSTEM LOCKED</p>
            <p className="text-red-400/70 font-mono text-xs text-center">{error}</p>
            <p className="text-jarvis-cyan/40 font-mono text-xs text-center">Restart JARVIS server to reset.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function JarvisApp() {
  const [logs, setLogs] = useState([]);
  const [activityState, setActivityState] = useState('STANDBY');
  const [liveTranscript, setLiveTranscript] = useState('> Click anywhere to activate mic...');
  const [textInput, setTextInput] = useState('');

  const recognitionRef = useRef(null);
  const isListeningRef = useRef(false);
  const isBusyRef = useRef(false);

  const sendCommand = (command) => {
    if (!command.trim()) return;
    // Immediately mark as not busy so mic can restart after this command
    isBusyRef.current = false;
    socket.emit('process_command', { command: command.trim().toLowerCase() });
    setTextInput('');
    setLiveTranscript('> Sending: ' + command.trim());
  };

  const startMic = () => {
    if (isListeningRef.current || isBusyRef.current) return;
    try { recognitionRef.current.start(); } catch { /* mic may already be active */ }
  };

  const stopMic = () => {
    if (!isListeningRef.current) return;
    try { recognitionRef.current.stop(); } catch { /* mic may already be stopped */ }
  };

  useEffect(() => {
    socket.connect();

    socket.on('system_log', (log) => {
      setLogs(prev => [log, ...prev].slice(0, 50));
    });

    socket.on('image_result', (data) => {
      window.open(data.url, '_blank');
    });

    socket.on('open_tab', (data) => {
      window.open(data.url, '_blank');
    });

    socket.on('activity_state', (data) => {
      setActivityState(data.state);
      if (data.state === 'PROCESSING' || data.state === 'SPEAKING') {
        isBusyRef.current = true;
        stopMic();
        setLiveTranscript(data.state === 'PROCESSING' ? '> Processing command...' : '> JARVIS is speaking...');
      } else {
        isBusyRef.current = false;
        setTimeout(() => startMic(), 500);
      }
    });

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      // Speech recognition not supported — no cleanup needed
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 3;
    recognitionRef.current = recognition;

    recognition.onstart = () => {
      isListeningRef.current = true;
      setLiveTranscript('> Listening...');
    };

    recognition.onend = () => {
      isListeningRef.current = false;
      if (!isBusyRef.current) setTimeout(() => startMic(), 300);
    };

    recognition.onresult = (event) => {
      let finalText = '';
      let interimText = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) finalText += event.results[i][0].transcript;
        else interimText += event.results[i][0].transcript;
      }
      if (interimText) setLiveTranscript('> ' + interimText);
      if (finalText) {
        const command = finalText.toLowerCase().trim()
          .replace(/hey jarvis/g, '').replace(/\bjarvis\b/g, '').trim();
        if (command.length > 0) {
          setLiveTranscript('> Sending: ' + command);
          sendCommand(command);
        }
      }
    };

    recognition.onerror = (event) => {
      isListeningRef.current = false;
      if (event.error === 'not-allowed') {
        setLiveTranscript('> Mic permission denied. Use text input below.');
        isBusyRef.current = true;
      } else if (event.error === 'no-speech') {
        if (!isBusyRef.current) setTimeout(() => startMic(), 300);
      } else if (event.error === 'aborted') {
        setLiveTranscript('> Click anywhere to activate mic...');
      }
    };

    const handleClick = () => {
      startMic();
      window.removeEventListener('click', handleClick);
    };
    window.addEventListener('click', handleClick);

    return () => {
      recognition.stop();
      window.removeEventListener('click', handleClick);
      socket.disconnect();
    };
  }, []);

  return (
    <div className="w-screen h-screen relative overflow-hidden">
      <div className="scanlines"></div>
      <Globe3D />
      <div className="relative z-10 w-full h-full flex flex-col pointer-events-none">
        <Navbar />
        <div className="flex-1 w-full pt-20 pb-4 px-8 flex flex-col justify-between">

          {/* Floating Arc Reactor */}
          <div className="absolute top-24 left-[350px] w-64 pointer-events-auto z-10 hidden xl:block">
            <IronManTopLeft />
          </div>

          {/* Floating Neural Core */}
          <div className="absolute top-24 right-[380px] w-64 pointer-events-auto z-10 hidden xl:block">
            <NeuralCore3D />
          </div>

          {/* Top Row */}
          <div className="flex justify-between items-start w-full">
            <div className="w-72 pointer-events-auto flex flex-col space-y-4">
              <SystemStatus />
              <GenderDetection />
            </div>

            {/* Center Top — Avatar with Radar */}
            <div className="flex-1 flex justify-center items-start pt-2 pointer-events-auto">
              <div className="relative flex justify-center items-center" style={{ width: 150, height: 150 }}>
                {/* Radar Sweep Background */}
                <div className="radar-sweep-bg"></div>
                {/* Avatar */}
                <div
                  className="relative rounded-full overflow-hidden border-2 border-jarvis-cyan/80 z-10"
                  style={{
                    width: 110, height: 110,
                    boxShadow: activityState === 'LISTENING'
                      ? '0 0 18px 6px #00ffd1, 0 0 40px 10px #00ffd155'
                      : activityState === 'SPEAKING'
                      ? '0 0 22px 8px #4ade80, 0 0 50px 14px #4ade8055'
                      : activityState === 'PROCESSING'
                      ? '0 0 18px 6px #60a5fa, 0 0 40px 10px #60a5fa55'
                      : '0 0 15px 4px #00ffd155',
                    animation: activityState === 'LISTENING' || activityState === 'SPEAKING'
                      ? 'pulse-ring 0.6s ease-in-out infinite alternate' : 'none',
                    transition: 'box-shadow 0.3s ease'
                  }}
                >
                  <img src={jarvisAvatar} alt="JARVIS" className="w-full h-full object-cover opacity-90" />
                </div>
              </div>
            </div>

            <div className="w-80 pointer-events-auto flex flex-col space-y-4">
              <SystemInfo />
              <DocumentAnalysis />
            </div>
          </div>

          {/* Bottom Row */}
          <div className="flex flex-col gap-3">
            {/* Text Command Input */}
            <div className="pointer-events-auto flex justify-center">
              <div className="flex items-center gap-2 bg-black/60 border border-jarvis-cyan/40 rounded-lg px-3 py-2 w-full max-w-2xl">
                <span className="text-jarvis-cyan/50 font-mono text-xs">CMD&gt;</span>
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') sendCommand(textInput); }}
                  placeholder="Type a command and press Enter..."
                  className="flex-1 bg-transparent text-jarvis-cyan font-mono text-sm outline-none placeholder-jarvis-cyan/30"
                />
                <button
                  onClick={() => sendCommand(textInput)}
                  className="text-jarvis-cyan/60 hover:text-jarvis-cyan font-orbitron text-xs border border-jarvis-cyan/30 px-2 py-1 rounded hover:border-jarvis-cyan/60 transition-all"
                >
                  SEND
                </button>
              </div>
            </div>

            {/* Bottom Panels */}
            <div className="flex justify-between items-end w-full">
              <div className="w-80 pointer-events-auto">
                <ActivityMonitor state={activityState} transcript={liveTranscript} />
              </div>
              <div className="flex-1 px-8 pointer-events-auto flex justify-center pb-2">
                <GreetingCard />
              </div>
              <div className="w-[22rem] pointer-events-auto">
                <SystemLog logs={logs} />
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

function App() {
  const [unlocked, setUnlocked] = useState(false);
  const [voiceSelected, setVoiceSelected] = useState(false);

  if (!unlocked) return <PasswordGate onUnlock={() => setUnlocked(true)} />;
  if (!voiceSelected) return <VoiceSelector onComplete={() => setVoiceSelected(true)} />;
  
  return <JarvisApp />;
}

export default App;
