'use client';

import { useState, useEffect } from 'react';

interface SimpleCompositeImageProps {
  croppedSrc: string;
  compositeSrc?: string;
  alt: string;
  town: string;
}

export default function SimpleCompositeImage({ croppedSrc, compositeSrc, alt, town }: SimpleCompositeImageProps) {
  const [hasError, setHasError] = useState(false);
  const [attemptedSrcs, setAttemptedSrcs] = useState<Set<string>>(new Set());

  // Determine which source to use
  const primarySrc = compositeSrc || croppedSrc;

  // Reset error state when props change
  useEffect(() => {
    setHasError(false);
  }, [croppedSrc, compositeSrc]);

  // Debug logging
  console.log('SimpleCompositeImage:', {
    croppedSrc,
    compositeSrc,
    primarySrc,
    hasError
  });

  const handleError = () => {
    console.log(`Image failed to load: ${primarySrc}`);
    setHasError(true);
  };

  if (hasError) {
    return (
      <div className="simple-composite-image-container">
        <div 
          className="image-container" 
          style={{ 
            width: '100%', 
            height: '450px',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            backgroundColor: '#f0f0f0',
            borderRadius: '2px',
            position: 'relative',
            flexDirection: 'column'
          }}
        >
          <p className="text-red-500 font-medium">Image could not be loaded</p>
          <p className="text-sm text-gray-500 mt-2">
            {primarySrc}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="simple-composite-image-container">
      <div 
        className="image-container" 
        style={{ 
          width: '100%', 
          height: '450px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          backgroundColor: '#ffffff',
          borderRadius: '2px',
          overflow: 'hidden',
          position: 'relative'
        }}
      >
        <img
          src={primarySrc}
          alt={alt}
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            objectFit: 'contain',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}
          onError={handleError}
        />
      </div>
      
      <div className="image-metadata" style={{
        marginTop: '8px',
        fontSize: '14px',
        color: '#666'
      }}>
        <div>Town: {town}</div>
        <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>
          Side-by-side view showing both cropped flag and original context
        </div>
      </div>
    </div>
  );
}