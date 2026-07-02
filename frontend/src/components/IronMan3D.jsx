import React from 'react';
import { HUDPanel } from './HUDPanel';

export const IronMan3D = () => {
  return (
    <HUDPanel title="MK-85 SUIT STATUS" className="h-48 overflow-hidden relative">
      <div className="absolute inset-0 pt-8 pb-2 px-2 flex justify-center items-center pointer-events-none">
        <iframe 
          title="Iron Man Suit" 
          frameBorder="0" 
          allowFullScreen 
          mozallowfullscreen="true" 
          webkitallowfullscreen="true" 
          allow="autoplay; fullscreen; xr-spatial-tracking" 
          xr-spatial-tracking="true" 
          execution-while-out-of-viewport="true" 
          execution-while-not-rendered="true" 
          web-share="true" 
          src="https://sketchfab.com/models/3732e7c4f4574ccfac7a9fba753a652d/embed?autostart=1&autospin=0.5&transparent=1&ui_animations=0&ui_infos=0&ui_stop=0&ui_inspector=0&ui_watermark_link=0&ui_watermark=0&ui_hint=0&ui_help=0&ui_settings=0&ui_vr=0&ui_fullscreen=0&ui_annotations=0"
          className="w-full h-full scale-[1.2] opacity-80"
          style={{ mixBlendMode: 'screen' }}
        ></iframe>
      </div>
      
      {/* Overlay UI elements to make it look like a scan */}
      <div className="absolute left-2 top-10 flex flex-col gap-1 text-[8px] font-mono text-jarvis-cyan/50 pointer-events-none">
        <span>PWR: 98%</span>
        <span>THR: OPT</span>
        <span>ARM: ON</span>
      </div>
      <div className="absolute right-2 top-10 flex flex-col gap-1 text-[8px] font-mono text-jarvis-cyan/50 text-right pointer-events-none">
        <span>INT: 100%</span>
        <span>SYS: NRM</span>
        <span>AI: ON</span>
      </div>
    </HUDPanel>
  );
};
