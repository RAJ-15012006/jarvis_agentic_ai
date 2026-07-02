import React from 'react';
// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';

export const HUDPanel = ({ children, className = '', title, borderColor = '' }) => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className={`hud-panel p-4 flex flex-col pointer-events-auto ${borderColor} ${className}`}
    >
      <div className="hud-panel-inner w-full h-full relative flex flex-col">
        {title && (
          <div className="border-b border-jarvis-cyan/30 pb-2 mb-3">
            <h2 className="text-jarvis-cyan font-orbitron tracking-widest text-sm uppercase">{title}</h2>
          </div>
        )}
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </div>
    </motion.div>
  );
};
