import React, { useState } from 'react';

export const DocumentAnalysis = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    const baseUrl = window.location.origin.includes('localhost') ? 'http://localhost:8000' : (window.location.origin.includes('jarvis.weblog') ? 'http://jarvis.weblog:8000' : window.location.origin);

    try {
      const res = await fetch(`${baseUrl}/api/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        setResult(data.analysis);
      } else {
        setError(data.error || 'Failed to analyze document.');
      }
    } catch {
      setError('Connection to JARVIS Core failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border border-jarvis-cyan/30 bg-black/60 rounded-lg p-4 shadow-[0_0_15px_rgba(0,255,209,0.05)] text-jarvis-cyan backdrop-blur-sm">
      <h3 className="font-orbitron text-xs tracking-widest font-bold text-center mb-3">INTELLIGENCE UPLOADER</h3>
      
      <div className="flex flex-col items-center gap-3">
        <label className="w-full flex flex-col items-center justify-center border border-dashed border-jarvis-cyan/30 rounded-lg p-4 cursor-pointer hover:bg-jarvis-cyan/5 transition-all">
          <svg className="w-8 h-8 text-jarvis-cyan/60 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
          </svg>
          <span className="font-rajdhani text-xs tracking-wider text-jarvis-cyan/80 text-center truncate w-full">
            {file ? file.name : "UPLOAD RESUME / PDF"}
          </span>
          <input type="file" accept=".pdf" onChange={handleFileChange} className="hidden" />
        </label>

        {file && !loading && (
          <button 
            onClick={handleUpload}
            className="w-full py-1.5 border border-jarvis-cyan text-jarvis-cyan font-orbitron text-xs hover:bg-jarvis-cyan hover:text-black rounded transition-all tracking-wider"
          >
            ANALYZE PDF
          </button>
        )}

        {loading && (
          <div className="flex items-center gap-2 py-1">
            <div className="w-4 h-4 border-2 border-jarvis-cyan border-t-transparent animate-spin rounded-full"></div>
            <span className="font-mono text-xs tracking-widest animate-pulse">ANALYZING CORE...</span>
          </div>
        )}

        {error && (
          <div className="text-red-400 font-mono text-[10px] text-center border border-red-500/20 bg-red-950/20 p-2 rounded w-full">
            {error}
          </div>
        )}
      </div>

      {/* Floating Result Modal */}
      {result && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/85 backdrop-blur-md pointer-events-auto p-4 md:p-8">
          <div className="bg-black/90 border border-jarvis-cyan/40 p-6 md:p-8 rounded-lg shadow-[0_0_40px_rgba(0,255,209,0.3)] max-w-3xl w-full h-[85vh] flex flex-col relative">
            <button 
              onClick={() => setResult(null)} 
              className="absolute top-4 right-4 text-jarvis-cyan hover:text-white font-orbitron text-xl transition-all"
            >
              X
            </button>
            <h2 className="text-xl md:text-2xl font-orbitron tracking-[0.2em] text-jarvis-cyan mb-4 border-b border-jarvis-cyan/20 pb-2 text-center">
              J.A.R.V.I.S. INTELLIGENCE ANALYSIS
            </h2>
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar font-rajdhani text-lg text-jarvis-cyan/90 leading-relaxed space-y-4 markdown-content text-left">
              {result.split('\n').map((line, idx) => {
                if (line.startsWith('# ')) {
                  return <h1 key={idx} className="text-2xl font-bold font-orbitron text-jarvis-cyan mt-4">{line.replace('# ', '')}</h1>;
                }
                if (line.startsWith('## ')) {
                  return <h2 key={idx} className="text-xl font-bold font-orbitron text-jarvis-cyan/90 mt-3">{line.replace('## ', '')}</h2>;
                }
                if (line.startsWith('### ')) {
                  return <h3 key={idx} className="text-lg font-bold font-orbitron text-jarvis-cyan/80 mt-2">{line.replace('### ', '')}</h3>;
                }
                if (line.startsWith('* ') || line.startsWith('- ')) {
                  return (
                    <div key={idx} className="ml-4 flex items-start gap-2 text-jarvis-cyan/80 my-1">
                      <span className="mt-2 w-1.5 h-1.5 rounded-full bg-jarvis-cyan shrink-0" />
                      <span>{line.replace(/^[*-]\s+/, '')}</span>
                    </div>
                  );
                }
                return <p key={idx} className="my-1">{line}</p>;
              })}
            </div>
            <div className="mt-4 border-t border-jarvis-cyan/15 pt-2 flex justify-between items-center text-[10px] text-jarvis-cyan/50 font-mono">
              <span>MODULE: PDF_ANALYSIS_V1</span>
              <span>CORE: LLAMA-3.3-70B-VERSATILE</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
