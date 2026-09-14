import React from 'react';

/**
 * @goose/ui Stub Module
 * 
 * NOTE: Minimal stub for the internal shared UI component package @goose/ui.
 */

export const CommandBar: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  return <div className="goose-command-bar">{children}</div>;
};

export default { CommandBar };
