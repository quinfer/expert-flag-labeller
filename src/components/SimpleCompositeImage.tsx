'use client';

import { useState } from 'react';

interface SimpleCompositeImageProps {
  croppedSrc: string;
  compositeSrc?: string;
  alt: string;
  town: string;
}

export default function SimpleCompositeImage({ croppedSrc, compositeSrc, alt, town }: SimpleCompositeImageProps) {
  const [showComposite, setShowComposite] = useState(false);
  const [hasError, setHasError] = useState(false);
  
  // Auto-generate a composite path if none is provided
  const deriveCompositePath = (path: string): string => {
    if (!path) return '';
    
    const parts = path.split('/');
    const filename = parts[parts.length - 1];
    
    // If not already a composite path, convert it
    if (!filename.startsWith('composite_')) {
      // Extract the base parts
      const baseParts = parts.slice(0, -1);
      const newFilename = `composite_${filename}`;
      return [...baseParts, newFilename].join('/');
    }
    
    return path;
  };
  
  // Use the provided compositeSrc or generate one
  const effectiveCompositeSrc = compositeSrc || deriveCompositePath(croppedSrc);

  // Simple toggle function
  const toggleView = () => {
    setShowComposite(!showComposite);
  };
  
  // Function to generate alternate URLs to try
  const getAlternatePaths = (originalPath) => {
    if (!originalPath) return [];
    
    // Original path with any leading slash removed
    const pathWithoutLeadingSlash = originalPath.startsWith('/') ? originalPath.substring(1) : originalPath;
    
    // Just the filename part
    const filename = originalPath.split('/').pop() || '';
    
    // Town part
    const townSegment = town.replace(/ /g, '_').toUpperCase();
    
    // Handle composite filenames
    let compositeFilename = filename;
    let regularFilename = filename;
    
    // If this is a composite path, extract the regular filename without 'composite_' prefix
    if (filename.startsWith('composite_')) {
      regularFilename = filename.substring('composite_'.length);
    } else {
      // If this is a regular path, create a composite filename by adding 'composite_' prefix
      compositeFilename = `composite_${filename}`;
    }
    
    // In production, the images are actually stored with composite_ prefix
    // Generate possible paths - prioritizing static folder with appropriate naming for production
    
    // For composite view, prioritize paths with composite prefix
    if (originalPath.includes('composite_') || originalPath === effectiveCompositeSrc) {
      return [
        originalPath,                                       // Original path exactly as provided
        pathWithoutLeadingSlash,                            // Without leading slash
        `/static/${townSegment}/composite_${regularFilename}`,  // Static folder path with composite prefix
        `/static/${townSegment}/${compositeFilename}`,     // Static folder path with explicitly handled name
        `/images/${townSegment}/composite_${regularFilename}`, // Images folder with composite prefix
        `../static/${townSegment}/composite_${regularFilename}`, // Relative path with composite prefix
        `/public/static/${townSegment}/composite_${regularFilename}`, // With public and composite prefix
        `/public/images/${townSegment}/composite_${regularFilename}`, // With public and composite prefix
        `static/${townSegment}/composite_${regularFilename}`, // No leading slash, with composite prefix
        `/expert-flag-labeler${originalPath}`,              // With project name
      ];
    } 
    // For regular view (non-composite), try both with and without composite prefix
    // since our copy script may have only copied composite versions
    else {
      return [
        originalPath,                                  // Original path exactly as provided
        pathWithoutLeadingSlash,                       // Without leading slash
        `/static/${townSegment}/${filename}`,          // Static folder path with original filename
        `/static/${townSegment}/composite_${filename}`, // Try the composite version in case regular doesn't exist
        `/images/${townSegment}/${filename}`,          // Reconstructed path
        `../static/${townSegment}/${filename}`,        // Relative static path
        `/public/static/${townSegment}/${filename}`,   // With public/static
        `/public/images/${townSegment}/${filename}`,   // With public/images
        `static/${townSegment}/${filename}`,           // Static with no leading slash
        `/expert-flag-labeler${originalPath}`,         // With project name
      ];
    }
  };
  
  // For debug purposes
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [currentCompositeIndex, setCurrentCompositeIndex] = useState(0);
  
  const alternateCroppedPaths = getAlternatePaths(croppedSrc);
  const alternateCompositePaths = getAlternatePaths(effectiveCompositeSrc);
  
  const currentCroppedPath = alternateCroppedPaths[currentImageIndex];
  const currentCompositePath = alternateCompositePaths[currentCompositeIndex];
  
  const tryNextPath = () => {
    if (showComposite) {
      setCurrentCompositeIndex((prev) => (prev + 1) % alternateCompositePaths.length);
    } else {
      setCurrentImageIndex((prev) => (prev + 1) % alternateCroppedPaths.length);
    }
  };
  
  return (
    <div className="simple-composite-image-container">
      
      {/* Image display - Clean container with more height for full-width layout */}
      <div className="image-container" style={{ 
        width: '100%', 
        height: '450px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#ffffff',
        borderRadius: '2px',
        overflow: 'hidden'
      }}>
        {/* We now use the same image for both views, but adjust CSS for different displays */}
      {showComposite ? (
          <img
            src={currentCompositePath}
            alt={`Side-by-side view of ${alt}`}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
            }}
            onError={(e) => {
              console.error(`Failed to load composite image: ${currentCompositePath}`);
              // If we've tried all paths and none worked, use a fallback
              if (currentCompositeIndex >= alternateCompositePaths.length - 1) {
                console.log("Tried all paths for composite image, checking if static path was included");
                
                // Check if we tried a path with /static/ in it
                const triedStaticPath = alternateCompositePaths.some(p => p.includes('/static/'));
                
                // If we haven't tried a static path explicitly (which might happen if the 
                // original paths aren't properly formatted), try static paths directly
                if (!triedStaticPath) {
                  const townSegment = town.replace(/ /g, '_').toUpperCase();
                  const filename = effectiveCompositeSrc.split('/').pop() || '';
                  
                  // Ensure we're using the composite_ prefix for composite view
                  let filenameToUse = filename;
                  if (!filenameToUse.startsWith('composite_')) {
                    filenameToUse = `composite_${filenameToUse}`;
                  }
                  
                  // Try direct static path with composite_ prefix
                  const staticPath = `/static/${townSegment}/${filenameToUse}`;
                  console.log("Trying direct static path for composite:", staticPath);
                  e.currentTarget.src = staticPath;
                  return;
                }
                
                // Only use sample images as a last resort
                // Sample side-by-side images
                const sampleSideBySideImages = [
                  'https://quinfer.github.io/flag-examples/side-by-side/example1.jpg',
                  'https://quinfer.github.io/flag-examples/side-by-side/example2.jpg',
                  'https://quinfer.github.io/flag-examples/side-by-side/example3.jpg'
                ];
                
                // Regular sample images
                const regularSamples = [
                  'https://quinfer.github.io/flag-examples/union-jack/example1.jpg',
                  'https://quinfer.github.io/flag-examples/ulster-banner/example1.jpg',
                  'https://quinfer.github.io/flag-examples/irish-tricolour/example1.jpg'
                ];
                
                // Select a sample image based on the original filename
                const nameHash = currentCompositePath.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
                
                // Try side-by-side first, then fall back to regular samples
                const sampleIndex = nameHash % regularSamples.length;
                e.currentTarget.src = regularSamples[sampleIndex];
                
                // Add indicator that this is a sample image
                const parent = e.currentTarget.parentNode;
                if (parent) {
                  const textNode = document.createElement('div');
                  textNode.style.position = 'absolute';
                  textNode.style.bottom = '10px';
                  textNode.style.left = '0';
                  textNode.style.right = '0';
                  textNode.style.textAlign = 'center';
                  textNode.style.background = 'rgba(0, 0, 0, 0.7)';
                  textNode.style.color = 'white';
                  textNode.style.padding = '5px';
                  textNode.innerText = '⚠️ Sample image shown (side-by-side view not available in production)';
                  parent.appendChild(textNode);
                }
              } else {
                // Try next path
                setCurrentCompositeIndex(prev => prev + 1);
              }
            }}
          />
        ) : (
          <div style={{
            position: 'relative',
            width: '100%',
            height: '100%',
            overflow: 'hidden'
          }}>
            <img
              src={currentCompositePath} // Use composite image for both views
              alt={alt}
              style={{
                maxWidth: '200%', // Zoom in to show just the left part
                maxHeight: '100%',
                objectFit: 'contain',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                objectPosition: 'left center', // Focus on the left part of the image (cropped view)
                transform: 'scale(1.6)', // Zoom in slightly
                transformOrigin: 'left center' // Zoom from the left
              }}
              onError={(e) => {
                console.error(`Failed to load image for cropped view: ${currentCompositePath}`);
              
                // Try the same fallback logic we use for composite view
                const townSegment = town.replace(/ /g, '_').toUpperCase();
                const filename = croppedSrc.split('/').pop() || '';
                
                // Use composite_ prefix since that's all we have in static
                const staticPathWithComposite = `/static/${townSegment}/composite_${filename}`;
                console.log("Trying direct composite path for cropped view:", staticPathWithComposite);
                
                e.currentTarget.src = staticPathWithComposite;
                
                // If we still fail, use a sample image as a last resort
                e.currentTarget.onerror = () => {
                  console.log("All attempts failed, using sample image");
                  // Clear error handler to prevent infinite loops
                  e.currentTarget.onerror = null;
                  
                  // Use sample images as last resort
                  const sampleImages = [
                    'https://quinfer.github.io/flag-examples/union-jack/example1.jpg',
                    'https://quinfer.github.io/flag-examples/ulster-banner/example1.jpg',
                    'https://quinfer.github.io/flag-examples/irish-tricolour/example1.jpg',
                    'https://quinfer.github.io/flag-examples/apprentice-boys/example1.jpg',
                    'https://quinfer.github.io/flag-examples/orange-order/example1.jpg'
                  ];
                  
                  // Pick a consistent sample image based on the image filename
                  const nameHash = croppedSrc.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
                  const sampleIndex = nameHash % sampleImages.length;
                  e.currentTarget.src = sampleImages[sampleIndex];
                };
              }}
              
              // Add an indicator that this is a sample image
              const parent = e.currentTarget.parentNode;
              if (parent) {
                const textNode = document.createElement('div');
                textNode.style.position = 'absolute';
                textNode.style.bottom = '10px';
                textNode.style.left = '0';
                textNode.style.right = '0';
                textNode.style.textAlign = 'center';
                textNode.style.background = 'rgba(0, 0, 0, 0.7)';
                textNode.style.color = 'white';
                textNode.style.padding = '5px';
                textNode.innerText = '⚠️ Sample image shown in production (actual image not available)';
                parent.appendChild(textNode);
              }
            }}
          />
        )}
      </div>
      
      {/* Invisible buttons that the main UI will call via querySelector */}
      <div style={{ display: 'none' }}>
        {/* Hidden button for toggling view */}
        <button
          onClick={toggleView}
          className="toggle-button toggle-composite-view"
        >
          Toggle View
        </button>
        
        {/* Hidden button for trying next path */}
        <button
          onClick={tryNextPath}
          className="try-next-path"
        >
          Try Next Path
        </button>
        
        {/* Hidden button for loading test image */}
        <button
          onClick={() => {
            // Force load the hardcoded test image
            if (showComposite) {
              setCurrentCompositeIndex(8); // Index of hardcoded test image
            } else {
              setCurrentImageIndex(8); // Index of hardcoded test image
            }
          }}
          className="force-test-image"
        >
          Force Test Image
        </button>
      </div>
      
      {/* Minimalist status indicator - show view type whenever composite view is active */}
      {showComposite && (
        <div style={{ 
          marginTop: '4px',
          fontSize: '11px',
          textAlign: 'right',
          color: '#6c757d'
        }}>
          Side-by-Side View Active
        </div>
      )}
      
      {/* Basic metadata */}
      <div className="image-metadata" style={{
        marginTop: '8px',
        fontSize: '14px',
        color: '#666'
      }}>
        <div>Town: {town}</div>
      </div>
    </div>
  );
}