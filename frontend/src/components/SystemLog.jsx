import React from 'react';
import { HUDPanel } from './HUDPanel';

export const SystemLog = ({ logs = [] }) => {
  return (
    <HUDPanel title="System Log" className="h-40">
      <div className="flex flex-col-reverse h-full overflow-y-auto space-y-reverse space-y-1 font-mono text-[10px] sm:text-xs">
        {logs.map((log, i) => {
          const logKey = `${log.time}-${log.type}-${log.message}-${i}`;
          return (
            <div key={logKey} className={`flex space-x-2 log-entry-anim ${log.type === 'error' ? 'text-red-400 drop-shadow-[0_0_5px_rgba(248,113,113,0.8)]' : log.type === 'user' ? 'text-white drop-shadow-[0_0_3px_rgba(255,255,255,0.8)]' : 'text-jarvis-cyan drop-shadow-[0_0_5px_rgba(0,255,209,0.8)]'}`}>
              <span className="text-jarvis-cyan/60 shrink-0">[{log.time}]</span>
              <span className="break-words whitespace-normal">{log.type === 'user' ? 'USR >' : 'SYS >'} {log.message}</span>
            </div>
          );
        })}
        {logs.length === 0 && (
          <div className="text-jarvis-cyan/40">SYSTEM LOG INITIALIZED... WAITING FOR EVENTS.</div>
        )}
      </div>
    </HUDPanel>
  );
};
