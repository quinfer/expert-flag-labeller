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
    
    // For the composite image, ensure we're using the composite_ prefix if needed
    let compositeFilename = filename;
    if (!filename.startsWith('composite_') && originalPath.includes('composite_')) {
      // Extract the composite filename from the path
      const parts = originalPath.split('/');
      compositeFilename = parts[parts.length - 1];
    }
    
    // Generate possible paths
    return [
      originalPath,                                  // Original path exactly as provided
      pathWithoutLeadingSlash,                       // Without leading slash
      `/images/${townSegment}/${filename}`,          // Reconstructed path
      `../images/${townSegment}/${filename}`,        // Relative path 
      `/public/images/${townSegment}/${filename}`,   // With public
      `public/images/${townSegment}/${filename}`,    // With public, no leading slash
      `./public/images/${townSegment}/${filename}`,  // With ./ prefix
      `/expert-flag-labeler${originalPath}`,         // With project name
    ];
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
                // Try to load a sample side-by-side image from GitHub Pages instead
                // Sample side-by-side images (would need to be hosted somewhere)
                const sampleSideBySideImages = [
                  'https://quinfer.github.io/flag-examples/side-by-side/example1.jpg',
                  'https://quinfer.github.io/flag-examples/side-by-side/example2.jpg',
                  'https://quinfer.github.io/flag-examples/side-by-side/example3.jpg'
                ];
                
                // Use a fallback if side-by-side samples don't exist - a regular sample image
                const regularSamples = [
                  'https://quinfer.github.io/flag-examples/union-jack/example1.jpg',
                  'https://quinfer.github.io/flag-examples/ulster-banner/example1.jpg',
                  'https://quinfer.github.io/flag-examples/irish-tricolour/example1.jpg'
                ];
                
                // Select a sample image based on the original filename
                const nameHash = currentCompositePath.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
                
                // Try side-by-side first, then fall back to regular samples if that fails
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
          <img
            src={currentCroppedPath}
            alt={alt}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
            }}
            onError={(e) => {
              console.error(`Failed to load cropped image: ${currentCroppedPath}`);
              // Try to load a sample image from GitHub Pages instead
              // This uses predetermined sample images hosted on GitHub Pages
              const sampleImages = [
                'https://quinfer.github.io/flag-examples/union-jack/example1.jpg',
                'https://quinfer.github.io/flag-examples/ulster-banner/example1.jpg',
                'https://quinfer.github.io/flag-examples/irish-tricolour/example1.jpg',
                'https://quinfer.github.io/flag-examples/apprentice-boys/example1.jpg',
                'https://quinfer.github.io/flag-examples/orange-order/example1.jpg'
              ];
              
              // Pick a consistent sample image based on the image filename for demonstration
              const nameHash = croppedSrc.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
              const sampleIndex = nameHash % sampleImages.length;
              e.currentTarget.src = sampleImages[sampleIndex];
              
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