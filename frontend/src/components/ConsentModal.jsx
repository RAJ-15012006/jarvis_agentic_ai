import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export const ConsentModal = ({ isOpen, onYes, onNo }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md pointer-events-auto">
          {/* Cybernetic Grid Background */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#00ffcc05_1px,transparent_1px),linear-gradient(to_bottom,#00ffcc05_1px,transparent_1px)] bg-[size:30px_30px]" />

          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: 'spring', damping: 20 }}
            className="relative border border-jarvis-cyan/40 bg-black/90 p-8 rounded-xl max-w-lg w-full mx-4 text-center overflow-hidden"
            style={{
              boxShadow: '0 0 50px 10px rgba(0, 255, 209, 0.2), inset 0 0 20px 2px rgba(0, 255, 209, 0.1)',
            }}
          >
            {/* Glowing Corner Elements */}
            <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-jarvis-cyan" />
            <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-jarvis-cyan" />
            <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-jarvis-cyan" />
            <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-jarvis-cyan" />

            {/* Pulsing Arc Reactor Core Logo */}
            <div className="flex justify-center mb-6">
              <div className="relative w-20 h-20 rounded-full border border-jarvis-cyan/30 flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border-2 border-dashed border-jarvis-cyan/40 animate-[spin_10s_linear_infinite]" />
                <div className="absolute w-16 h-16 rounded-full border border-jarvis-cyan/50 animate-pulse" />
                <div className="w-10 h-10 rounded-full bg-radial-gradient from-jarvis-cyan to-blue-600 shadow-[0_0_20px_#00ffd1]" />
              </div>
            </div>

            <h2 className="font-orbitron text-jarvis-cyan text-lg tracking-[0.2em] mb-4 uppercase">
              SYSTEM CONCURRENCE REQUIRED
            </h2>

            <p className="font-rajdhani text-white text-xl tracking-wide leading-relaxed mb-8">
              "Hello, I am Jarvis. How can I help you today? Do you need my help?"
            </p>

            <div className="flex gap-6 justify-center">
              {/* YES Button */}
              <button
                onClick={onYes}
                className="flex-1 py-3 border border-jarvis-cyan text-jarvis-cyan hover:bg-jarvis-cyan hover:text-black font-rajdhani text-lg font-bold tracking-widest transition-all uppercase rounded shadow-[0_0_15px_rgba(0,255,209,0.2)] hover:shadow-[0_0_25px_rgba(0,255,209,0.5)]"
              >
                YES
              </button>

              {/* NO Button */}
              <button
                onClick={onNo}
                className="flex-1 py-3 border border-red-500 text-red-500 hover:bg-red-500 hover:text-black font-rajdhani text-lg font-bold tracking-widest transition-all uppercase rounded shadow-[0_0_15px_rgba(239,68,68,0.2)] hover:shadow-[0_0_25px_rgba(239,68,68,0.5)]"
              >
                NO
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
