'use client';

import { useState } from 'react';

interface SimpleCompositeImageProps {
  croppedSrc: string;
  compositeSrc?: string;
  alt: string;
  town: string;
}

export default function SimpleCompositeImage({ croppedSrc, compositeSrc, alt, town }: SimpleCompositeImageProps) {
  const [hasError, setHasError] = useState(false);
  const [currentSrc, setCurrentSrc] = useState(compositeSrc || croppedSrc);

  // Debug logging
  console.log('SimpleCompositeImage:', {
    croppedSrc,
    compositeSrc,
    currentSrc,
    hasError
  });

  const handleError = () => {
    console.log(`Image failed to load: ${currentSrc}`);
    
    if (currentSrc === compositeSrc && croppedSrc !== compositeSrc) {
      // Try the cropped source as fallback
      console.log(`Trying fallback: ${croppedSrc}`);
      setCurrentSrc(croppedSrc);
    } else {
      // All attempts failed
      console.log('All image sources failed, showing error state');
      setHasError(true);
    }
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
            {currentSrc}
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
          src={currentSrc}
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