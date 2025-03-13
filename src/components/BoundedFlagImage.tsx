'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { staticImages } from '../data/images';

interface BoundedFlagImageProps {
  src: string;
  alt?: string;
  town?: string;
  showComposite?: boolean;
  setShowComposite?: React.Dispatch<React.SetStateAction<boolean>>;
  imageData?: {
    confidence?: number;
    distance_hint?: string;
    relative_size?: number;
  };
}

const BoundedFlagImage = ({ 
  src, 
  alt = "Flag image", 
  town = "Unknown location",
  showComposite = false,
  setShowComposite = () => {},
  imageData = {}
}: BoundedFlagImageProps) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [images, setImages] = useState(staticImages || []);
  
  // Guard against empty src
  if (!src) {
    return (
      <div className="bounded-flag-image-placeholder" style={{ 
        width: '100%', 
        height: '200px', 
        backgroundColor: '#f0f0f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <span>No image available for {town}</span>
      </div>
    );
  }
  
  // Function to try multiple path formats
  const attemptLoadWithAlternatePaths = () => {
    // Original path with any leading slash removed
    const pathWithoutLeadingSlash = src.startsWith('/') ? src.substring(1) : src;
    
    // Just the filename part
    const filename = src.split('/').pop() || '';
    
    // Town/filename without public folder
    const townAndFilename = `images/${town}/${filename}`;
    
    console.log("Trying alternate paths for image:", {
      original: src,
      withoutLeadingSlash: pathWithoutLeadingSlash,
      townAndFilename: townAndFilename,
      filename: filename
    });
    
    // Try all possible paths in sequence
    const paths = [
      src,                    // Original path
      pathWithoutLeadingSlash, // Without leading slash
      townAndFilename,         // images/TOWN/filename
      `/images/${town}/${filename}`, // /images/TOWN/filename
      `/expert-flag-labeler${src}`,  // With repo name prefix
      filename                 // Just the filename
    ];
    
    return paths;
  };
  
  const [alternatePathIndex, setAlternatePathIndex] = useState(0);
  const alternatePaths = attemptLoadWithAlternatePaths();
  const currentPath = alternatePaths[alternatePathIndex] || src;
  
  // This method will try to find the actual image file on the server
  const checkImageExists = (imagePath) => {
    console.log(`[BoundedFlagImage] Checking if image exists: ${imagePath}`);
    // In a real implementation, you could make a HEAD request to check
    // But for now we'll just log it
    return true; // Assume it exists for now
  };
  
  // Check if any images exist at page load
  useEffect(() => {
    const firstImage = alternatePaths[0];
    console.log(`[BoundedFlagImage] Initial image check for: ${firstImage}`);
    checkImageExists(firstImage);
  }, []);
  
  return (
    <div className="bounded-flag-image-container" style={{ position: 'relative', minHeight: '200px' }}>
      {isLoading && (
        <div className="loading-indicator" style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f5f5f5',
          zIndex: 5
        }}>Loading image...</div>
      )}
      
      <div style={{ padding: '8px', backgroundColor: '#f0f0f0', marginBottom: '10px', fontSize: '12px' }}>
        Debug info: Using path {alternatePathIndex + 1}/{alternatePaths.length}: {currentPath}
      </div>
      
      <img
        src={currentPath}
        alt={alt || `Flag in ${town}`}
        onLoad={() => {
          console.log(`[BoundedFlagImage] Successfully loaded image: ${currentPath}`);
          setIsLoading(false);
        }}
        onError={(e) => {
          console.error(`[BoundedFlagImage] Failed to load image: ${currentPath}`);
          
          // Try next alternate path if available
          if (alternatePathIndex < alternatePaths.length - 1) {
            setAlternatePathIndex(alternatePathIndex + 1);
            console.log(`[BoundedFlagImage] Trying alternate path (${alternatePathIndex + 1}/${alternatePaths.length}):`, 
              alternatePaths[alternatePathIndex + 1]);
          } else {
            setHasError(true);
            setIsLoading(false);
            console.error(`[BoundedFlagImage] All paths failed for image: ${src}`);
          }
        }}
        style={{
          display: hasError ? 'none' : 'block',
          width: '100%',
          height: 'auto',
          maxHeight: '300px',
          objectFit: 'contain',
          opacity: isLoading ? 0.5 : 1,
          transition: 'opacity 0.3s ease'
        }}
      />
      
      {hasError && (
        <div className="error-message" style={{
          padding: '1rem',
          backgroundColor: '#ffeeee',
          border: '1px solid #ffcccc',
          borderRadius: '4px',
          marginTop: '0.5rem'
        }}>
          <p style={{ fontWeight: 'bold' }}>Failed to load image from {town}</p>
          <p style={{ fontSize: '12px', marginTop: '5px' }}>Original path: {src}</p>
          <div style={{ fontSize: '12px', marginTop: '5px' }}>
            Tried paths:
            <ul style={{ marginLeft: '20px', marginTop: '5px' }}>
              {alternatePaths.map((path, idx) => (
                <li key={idx} style={{ marginBottom: '2px' }}>{path}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
      
      {/* Only show toggle if composite is available */}
      {showComposite && (
        <button
          type="button"
          onClick={() => setShowComposite(false)}
          className="mt-2 px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
        >
          Show Cropped Only
        </button>
      )}
      
      <div className="mt-2 text-sm text-gray-700">
        <div>Town: {town || 'Unknown'}</div>
        {imageData?.confidence !== undefined && (
          <div>Confidence: {`${(imageData.confidence * 100).toFixed(0)}%`}</div>
        )}
        {imageData?.distance_hint && <div>{imageData.distance_hint}</div>}
      </div>
    </div>
  );
};

export default BoundedFlagImage;
