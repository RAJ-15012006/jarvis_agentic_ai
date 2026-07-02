import React, { useState, useEffect } from 'react';
// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';

export const GreetingCard = () => {
  const [recommendation, setRecommendation] = useState("Initializing ML predictive core...");

  useEffect(() => {
    fetch(window.location.origin.includes('localhost') ? 'http://localhost:8000/api/recommendation' : '/api/recommendation')
      .then(res => res.json())
      .then(data => setRecommendation(data.recommendation))
      .catch(() => setRecommendation("Standing by for instructions."));
  }, []);

  const hour = new Date().getHours();
  const greeting =
    hour >= 0  && hour < 12 ? 'GOOD MORNING, RAJ.' :
    hour >= 12 && hour < 16 ? 'GOOD AFTERNOON, RAJ.' :
    hour >= 16 && hour < 20 ? 'GOOD EVENING, RAJ.' :
    'GOOD NIGHT, RAJ.';

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 1, delay: 0.5, ease: "easeOut" }}
      className="bg-black/40 backdrop-blur-sm border border-jarvis-cyan/30 p-6 rounded-lg pointer-events-auto 
                 shadow-[0_0_20px_rgba(0,255,209,0.15)] flex flex-col items-center justify-center text-center max-w-2xl mx-auto w-full"
    >
      <h2 className="text-xl md:text-2xl font-orbitron tracking-[0.15em] text-jarvis-cyan mb-2">
        {greeting}
      </h2>
      <p className="font-rajdhani text-jarvis-cyan/80 text-lg tracking-wide min-h-[40px] flex items-center justify-center text-center">
        {recommendation}
      </p>
    </motion.div>
  );
};
