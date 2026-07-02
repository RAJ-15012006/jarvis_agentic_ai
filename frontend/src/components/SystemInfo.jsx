import React, { useState, useEffect } from 'react';
import { HUDPanel } from './HUDPanel';

const loadTime = Date.now();

export const SystemInfo = () => {
  const [time, setTime] = useState(new Date());
  const [startTime] = useState(loadTime);
  const [uptime, setUptime] = useState('00:00:00');

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setTime(now);
      
      const diffMs = now.getTime() - startTime;
      const secs = Math.floor(diffMs / 1000) % 60;
      const mins = Math.floor(diffMs / (1000 * 60)) % 60;
      const hours = Math.floor(diffMs / (1000 * 60 * 60));
      
      const format = (num) => String(num).padStart(2, '0');
      setUptime(`${format(hours)}:${format(mins)}:${format(secs)}`);
    }, 1000);
    return () => clearInterval(timer);
  }, [startTime]);

  return (
    <HUDPanel title="System Info" className="h-48">
      <div className="flex flex-col space-y-4 font-mono text-sm mt-2">
        
        <div className="flex justify-between items-end border-b border-jarvis-cyan/20 pb-2">
          <span className="text-jarvis-cyan/60 text-xs">LOCAL TIME</span>
          <span className="text-xl text-jarvis-cyan">
            {time.toLocaleTimeString('en-US', { hour12: false })}
          </span>
        </div>

        <div className="flex justify-between items-end border-b border-jarvis-cyan/20 pb-2">
          <span className="text-jarvis-cyan/60 text-xs">DATE</span>
          <span className="text-jarvis-cyan">
           {time.toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase()}
          </span>
        </div>

        <div className="flex justify-between items-end">
          <span className="text-jarvis-cyan/60 text-xs">UPTIME</span>
          <span className="text-jarvis-cyan border border-jarvis-cyan/30 px-2 rounded bg-jarvis-cyan/10">
            {uptime}
          </span>
        </div>

      </div>
    </HUDPanel>
  );
};
