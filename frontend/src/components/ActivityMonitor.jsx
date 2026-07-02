import React from 'react';
import { HUDPanel } from './HUDPanel';
// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';

export const ActivityMonitor = ({ state = 'STANDBY', transcript = '' }) => {

  const stateConfig = {
    LISTENING:  { color: '#facc15', label: 'LISTENING' },
    PROCESSING: { color: '#60a5fa', label: 'PROCESSING' },
    SPEAKING:   { color: '#4ade80', label: 'SPEAKING'  },
    STANDBY:    { color: '#00ffd1', label: 'STANDBY'   },
  };

  const { color, label } = stateConfig[state] || stateConfig.STANDBY;

  return (
    <HUDPanel title="Activity Monitor" className="h-48">
      <div className="flex flex-col h-full justify-between">

        <div className="flex items-center space-x-3 mb-3">
          <motion.div
            animate={{ opacity: [0.3, 1, 0.3], scale: state !== 'STANDBY' ? [1, 1.3, 1] : 1 }}
            transition={{ duration: state === 'STANDBY' ? 2 : 0.6, repeat: Infinity }}
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}` }}
          />
          <span className="font-orbitron tracking-widest text-sm" style={{ color }}>
            {label}
          </span>
        </div>

        <div className="flex-1 bg-black/40 rounded border border-jarvis-cyan/20 p-2 overflow-y-auto">
          <p className="text-xs font-mono" style={{ color: state === 'LISTENING' ? '#facc15' : '#00ffd1cc' }}>
            {transcript || '> Awaiting audio input...'}
          </p>
        </div>

      </div>
    </HUDPanel>
  );
};
