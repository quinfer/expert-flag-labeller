'use client'

import { useEffect } from 'react'

export function HydrationSuppressor() {
  useEffect(() => {
    if (process.env.NODE_ENV === 'production') {
      const originalConsoleError = console.error;
      console.error = (...args) => {
        if (args[0]?.includes?.('Warning: Text content did not match') || 
            args[0]?.includes?.('Warning: Prop') || 
            args[0]?.includes?.('Warning: Attribute')) {
          return;
        }
        originalConsoleError(...args);
      };
    }
  }, []);
  
  return null;
}
