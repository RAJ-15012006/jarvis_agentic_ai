import React from 'react';
import { HUDPanel } from './HUDPanel';

export const SystemStatus = () => {
  const agents = [
    { name: 'SPEECH REC', status: 'ONLINE' },
    { name: 'BRAIN ROUTER', status: 'ONLINE' },
    { name: 'LOCAL LLM', status: 'OFFLINE' },
    { name: 'WEB SEARCH', status: 'ONLINE' },
    { name: 'AUTOMATION', status: 'ONLINE' },
  ];

  return (
    <HUDPanel title="System Status" className="h-64">
      <div className="flex flex-col space-y-3 mt-2">
        {agents.map((agent, i) => (
          <div key={i} className="flex items-center justify-between text-xs font-mono">
            <span className="text-jarvis-cyan/80">{agent.name}</span>
            <div className="flex items-center space-x-2">
              <span className={agent.status === 'ONLINE' ? 'text-green-400' : 'text-red-400'}>
                {agent.status}
              </span>
              <div className={`w-2 h-2 rounded-full ${agent.status === 'ONLINE' ? 'bg-green-400' : 'bg-red-400'}`}></div>
            </div>
          </div>
        ))}
      </div>
    </HUDPanel>
  );
};
