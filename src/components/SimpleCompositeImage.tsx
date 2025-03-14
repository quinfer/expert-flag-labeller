'use client';

// No state management needed

interface SimpleCompositeImageProps {
  croppedSrc: string;
  compositeSrc?: string;
  alt: string;
  town: string;
}

export default function SimpleCompositeImage({ croppedSrc, compositeSrc, alt, town }: SimpleCompositeImageProps) {
  // Add logging to debug image loading
  console.log('SimpleCompositeImage props:', { croppedSrc, compositeSrc, alt, town });
  // Function to generate paths with the composite_ prefix
  const getCompositePaths = () => {
    // Get town in consistent format
    const townSegment = town.replace(/ /g, '_').toUpperCase();
    
    // Extract filename from path
    const pathParts = croppedSrc.split('/');
    const filename = pathParts[pathParts.length - 1];
    
    // Ensure we have a composite_ prefix version
    const compositeFilename = filename.startsWith('composite_') 
      ? filename 
      : `composite_${filename}`;
      
    // Return paths in order of priority
    return [
      `/static/${townSegment}/${compositeFilename}`,
      `static/${townSegment}/${compositeFilename}`,
      `/images/${townSegment}/${compositeFilename}`,
      compositeSrc || ''
    ].filter(p => p); // Filter out empty strings
  };
  
  // Get all possible paths
  const compositePaths = getCompositePaths();
  const imagePath = compositePaths[0];
  
  // Error handler for image loading
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    const currentSrc = img.src;
    console.error(`Failed to load image: ${currentSrc}`);
    
    // Find the next path to try
    const currentPathIndex = compositePaths.findIndex(p => 
      currentSrc.includes(p) || p.includes(currentSrc.split('/').pop() || '')
    );
    
    if (currentPathIndex < compositePaths.length - 1) {
      // Try the next path
      const nextPath = compositePaths[currentPathIndex + 1];
      console.log(`Trying next path: ${nextPath}`);
      img.src = nextPath;
    } else {
      // We've tried all paths, use a fallback sample image
      console.log('All paths failed, using sample image');
      const sampleImages = [
        'https://quinfer.github.io/flag-examples/union-jack/example1.jpg',
        'https://quinfer.github.io/flag-examples/ulster-banner/example1.jpg',
        'https://quinfer.github.io/flag-examples/irish-tricolour/example1.jpg'
      ];
      
      // Pick a sample based on the filename hash for consistency
      const nameHash = croppedSrc.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const sampleIndex = nameHash % sampleImages.length;
      img.src = sampleImages[sampleIndex];
      
      // Add an indicator that this is a sample image
      const parent = img.parentNode;
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
        textNode.innerText = '⚠️ Sample image shown (original not available)';
        parent.appendChild(textNode);
      }
    }
  };

  return (
    <div className="simple-composite-image-container">
      {/* Image container with ample height */}
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
        {/* Always show the composite image at full size */}
        <img
          src={imagePath}
          alt={alt}
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            objectFit: 'contain',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}
          onError={handleImageError}
        />
      </div>
      
      {/* Basic metadata */}
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