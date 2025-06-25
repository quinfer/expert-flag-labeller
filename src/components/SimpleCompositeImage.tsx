'use client';

import { getImageUrl } from '@/lib/supabase';
import { useState } from 'react';

interface SimpleCompositeImageProps {
  croppedSrc: string;
  compositeSrc?: string;
  alt: string;
  town: string;
}

export default function SimpleCompositeImage({ croppedSrc, compositeSrc, alt, town }: SimpleCompositeImageProps) {
  const [imagePath, setImagePath] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [fallbackCount, setFallbackCount] = useState(0);
  
  // Generate image paths once on component mount
  const getCompositePaths = () => {
    const townSegment = town.replace(/ /g, '_').toUpperCase();
    
    // Check if we're already using a Supabase URL
    const isSupabaseUrl = croppedSrc.includes('supabase') && croppedSrc.includes('/storage/');
    
    // Extract filename from path (handle both Supabase URLs and local paths)
    const pathParts = croppedSrc.split('/');
    const filename = pathParts[pathParts.length - 1];
    
    // Check if we already have a specific compositeSrc provided
    if (compositeSrc) {
      // If we have a direct composite src, use it first
      return [compositeSrc, croppedSrc]; // Also try the original as fallback
    }
    
    // Detect if this is a cropped image that needs a composite
    const isBoxed = filename.includes('_boxed');
    const isBoxCropped = /_box\d+\.jpg$/.test(filename); // Matches _box0.jpg, _box1.jpg etc.
    
    // BOTH multi-box crops AND boxed images should show composite views for context
    const needsComposite = isBoxCropped || isBoxed;
    
    if (needsComposite) {
      // Create the composite filename
      const compositeFilename = `composite_${filename}`;
      
      // Generate Supabase Storage URL if we're using Supabase
      if (isSupabaseUrl) {
        // If the URL is from Supabase, extract the town and filename
        // and generate a new URL for the composite version
        return [
          // Replace the filename portion with the composite filename
          croppedSrc.replace(filename, compositeFilename)
        ];
      }
      
      // Otherwise, generate the composite URL from parameters
      const compositeUrl = getImageUrl(`${townSegment}/${compositeFilename}`);
      const originalSupabaseUrl = getImageUrl(`${townSegment}/${filename}`);
      
      // For local development, prioritize direct paths over Supabase URLs
      const isDevelopment = !isSupabaseUrl && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
      
      if (isDevelopment) {
        // In development, use direct paths first
        return [
          croppedSrc, // Original path provided by API
          compositeSrc || `${croppedSrc.replace(filename, `composite_${filename}`)}` // Try to construct composite path
        ].filter(Boolean);
      } else {
        // In production, use Supabase URLs
        return [
          compositeUrl,
          originalSupabaseUrl,
          croppedSrc // Fallback to original sources
        ].filter(Boolean);
      }
    } else {
      // For regular images (not from multi-box detections),
      // prioritize direct paths in development
      const isDevelopment = !isSupabaseUrl && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
      
      if (isDevelopment) {
        return [croppedSrc]; // Use the direct path provided
      } else if (isSupabaseUrl) {
        return [croppedSrc];
      } else {
        const supabaseUrl = getImageUrl(`${townSegment}/${filename}`);
        return [supabaseUrl, croppedSrc];
      }
    }
  };
  
  // Get all possible paths
  const compositePaths = getCompositePaths();
  
  // Initialize image path
  if (isLoading && compositePaths.length > 0) {
    setImagePath(compositePaths[0]);
    setIsLoading(false);
  }
  
  // Error handler for image loading
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    
    // Try next path if available
    if (fallbackCount < compositePaths.length - 1) {
      const nextIndex = fallbackCount + 1;
      const nextPath = compositePaths[nextIndex];
      setFallbackCount(nextIndex);
      setImagePath(nextPath);
      console.log(`Image load error, trying fallback #${nextIndex}: ${nextPath}`);
    } else {
      // We've tried all paths, use a fallback sample image
      const sampleImages = [
        'https://quinfer.github.io/flag-examples/union-jack/example1.jpg',
        'https://quinfer.github.io/flag-examples/ulster-banner/example1.jpg',
        'https://quinfer.github.io/flag-examples/irish-tricolour/example1.jpg'
      ];
      
      // Pick a sample based on the town name for consistency
      const nameHash = town.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const sampleIndex = nameHash % sampleImages.length;
      
      console.log(`All image paths failed, using sample image #${sampleIndex}`);
      setImagePath(sampleImages[sampleIndex]);
      
      // Add an error marker to the image container
      const parent = img.parentNode as HTMLElement;
      if (parent && !parent.querySelector('.image-error-indicator')) {
        const textNode = document.createElement('div');
        textNode.className = 'image-error-indicator';
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
        {/* Show the image */}
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