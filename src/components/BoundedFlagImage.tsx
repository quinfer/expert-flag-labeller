'use client';

import { useState, useEffect } from 'react';
// Import removed to avoid confusion with browser's Image constructor
import { staticImages } from '../data/images';

interface BoundedFlagImageProps {
  src: string;
  alt?: string;
  town?: string;
  showComposite?: boolean;
  setShowComposite?: React.Dispatch<React.SetStateAction<boolean>>;
  compositeImageSrc?: string;
  imageData?: {
    confidence?: number;
    distance_hint?: string;
    relative_size?: number;
    has_composite?: boolean;
    composite_image?: string;
  };
}

const BoundedFlagImage = ({ 
  src, 
  alt = "Flag image", 
  town = "Unknown location",
  showComposite = false,
  setShowComposite = () => {},
  compositeImageSrc,
  imageData = {}
}: BoundedFlagImageProps) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [images, setImages] = useState(staticImages || []);
  const [displayComposite, setDisplayComposite] = useState(showComposite);
  
  // Get the composite image source either from props or from imageData
  const compositeImage = compositeImageSrc || imageData?.composite_image;
  const hasComposite = !!compositeImage || !!imageData?.has_composite;
  
  // Debug logging
  useEffect(() => {
    if (hasComposite) {
      console.log(`[BoundedFlagImage] Image has composite data:`, {
        filename: imageData?.filename,
        composite_image: compositeImage,
        has_composite: imageData?.has_composite
      });
    }
  }, []);
  
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
  
  // Function to generate image paths for side-by-side composite image
  const getCompositePaths = (compositeImagePath) => {
    // Original path with any leading slash removed
    const pathWithoutLeadingSlash = compositeImagePath.startsWith('/') ? compositeImagePath.substring(1) : compositeImagePath;
    
    // Just the filename part
    const filename = compositeImagePath.split('/').pop() || '';
    
    // Town/filename without public folder
    const townAndFilename = `images/${town}/${filename}`;
    
    // Try all possible paths in sequence
    return [
      compositeImagePath,        // Original path
      pathWithoutLeadingSlash,   // Without leading slash
      townAndFilename,           // images/TOWN/filename
      `/images/${town}/${filename}`, // /images/TOWN/filename
      `/expert-flag-labeler${compositeImagePath}`,  // With repo name prefix
      filename                   // Just the filename
    ];
  };
  
  const [compositeAlternatePaths, setCompositeAlternatePaths] = useState([]);
  const [compositePathIndex, setCompositePathIndex] = useState(0);
  const [compositeLoading, setCompositeLoading] = useState(true);
  const [compositeError, setCompositeError] = useState(false);
  
  // Initialize composite paths when the component mounts
  useEffect(() => {
    if (compositeImage) {
      console.log(`[BoundedFlagImage] Initializing composite paths for: ${compositeImage}`);
      const paths = getCompositePaths(compositeImage);
      console.log(`[BoundedFlagImage] Generated ${paths.length} alternate paths for composite image`, paths);
      setCompositeAlternatePaths(paths);
      
      // Pre-check if the image exists using the HTML Image element (not Next.js Image)
      const img = new window.Image(); // Use the browser's Image constructor
      img.onload = () => {
        console.log(`[BoundedFlagImage] Successfully pre-loaded composite image: ${compositeImage}`);
      };
      img.onerror = () => {
        console.error(`[BoundedFlagImage] Failed to pre-load composite image: ${compositeImage}`);
      };
      img.src = compositeImage;
    }
  }, [compositeImage]);
  
  const currentCompositePath = compositeAlternatePaths[compositePathIndex] || '';

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
        {hasComposite && displayComposite && (
          <div>Composite path: {compositePathIndex + 1}/{compositeAlternatePaths.length}: {currentCompositePath}</div>
        )}
      </div>
      
      {/* Render either the composite image or the regular cropped image */}
      {hasComposite && displayComposite ? (
        // Show side-by-side composite image
        <img
          src={currentCompositePath}
          alt={`Side-by-side comparison of flag in ${town}`}
          onLoad={() => {
            console.log(`[BoundedFlagImage] Successfully loaded composite image: ${currentCompositePath}`);
            setCompositeLoading(false);
          }}
          onError={(e) => {
            console.error(`[BoundedFlagImage] Failed to load composite image: ${currentCompositePath}`);
            
            // Try next alternate path for composite if available
            if (compositePathIndex < compositeAlternatePaths.length - 1) {
              setCompositePathIndex(compositePathIndex + 1);
              console.log(`[BoundedFlagImage] Trying alternate composite path (${compositePathIndex + 1}/${compositeAlternatePaths.length}):`, 
                compositeAlternatePaths[compositePathIndex + 1]);
            } else {
              setCompositeError(true);
              setCompositeLoading(false);
              setDisplayComposite(false); // Fall back to regular image
              console.error(`[BoundedFlagImage] All paths failed for composite image: ${compositeImage}`);
            }
          }}
          style={{
            display: compositeError ? 'none' : 'block',
            width: '100%',
            height: 'auto',
            maxHeight: '300px',
            objectFit: 'contain',
            opacity: compositeLoading ? 0.5 : 1,
            transition: 'opacity 0.3s ease'
          }}
        />
      ) : (
        // Show regular cropped image
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
      )}
      
      {hasError && !displayComposite && (
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
      
      {/* Toggle button between regular and side-by-side view */}
      {hasComposite && (
        <button
          type="button"
          onClick={() => setDisplayComposite(!displayComposite)}
          className="mt-2 px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
        >
          {displayComposite ? "Show Cropped Only" : "Show Side-by-Side View"}
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
