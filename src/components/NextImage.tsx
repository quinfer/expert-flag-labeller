'use client';

import Image from 'next/image';
import { useState } from 'react';

interface NextImageProps {
  src: string;
  alt?: string;
  width?: number;
  height?: number;
  className?: string;
}

export default function NextImage({ 
  src, 
  alt = "Image", 
  width = 400, 
  height = 300, 
  className = "" 
}: NextImageProps) {
  const [error, setError] = useState(false);
  
  // Use a relative URL within the public directory
  // Remove leading slash if present to work with Next.js Image component
  const imageSrc = src.startsWith('/') ? src.substring(1) : src;
  
  return (
    <div className={`next-image-container ${className}`} style={{ position: 'relative' }}>
      <div style={{ 
        fontSize: '10px', 
        backgroundColor: '#eee', 
        padding: '4px', 
        marginBottom: '5px'
      }}>
        Using Next.js Image with src: {imageSrc}
      </div>
      
      {error ? (
        <div style={{ 
          width: width, 
          height: height, 
          backgroundColor: '#f8d7da', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          border: '1px solid #f5c6cb',
          color: '#721c24',
          padding: '1rem'
        }}>
          Failed to load image
        </div>
      ) : (
        <Image
          src={`/${imageSrc}`}
          alt={alt}
          width={width}
          height={height}
          style={{ objectFit: 'contain' }}
          onError={() => setError(true)}
          unoptimized
        />
      )}
    </div>
  );
}