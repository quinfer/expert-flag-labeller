'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';

export default function TestPath() {
  const [loaded, setLoaded] = useState<Record<string, boolean>>({});
  
  // Sample image paths to test
  const testPaths = [
    '/images/ANTRIM/22GmnyT9QDWUQQSkBZvBgA_180_box0.jpg',
    'images/ANTRIM/22GmnyT9QDWUQQSkBZvBgA_180_box0.jpg',
    '../images/ANTRIM/22GmnyT9QDWUQQSkBZvBgA_180_box0.jpg',
    '/public/images/ANTRIM/22GmnyT9QDWUQQSkBZvBgA_180_box0.jpg',
    '/expert-flag-labeler/images/ANTRIM/22GmnyT9QDWUQQSkBZvBgA_180_box0.jpg',
  ];
  
  const handleImageLoad = (path: string) => {
    console.log(`Image loaded successfully: ${path}`);
    setLoaded(prev => ({ ...prev, [path]: true }));
  };
  
  const handleImageError = (path: string) => {
    console.error(`Image failed to load: ${path}`);
    setLoaded(prev => ({ ...prev, [path]: false }));
  };
  
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Image Path Testing</h1>
      
      <div className="grid gap-6">
        {testPaths.map((path, index) => (
          <div key={index} className="border p-4 rounded">
            <h2 className="text-lg font-semibold mb-2">Test {index + 1}</h2>
            <pre className="bg-gray-100 p-2 mb-4 overflow-x-auto">{path}</pre>
            
            <div className="border p-4">
              <p className="mb-2">Regular img tag:</p>
              <img 
                src={path}
                alt={`Test ${index + 1}`}
                style={{ maxWidth: '300px', height: 'auto' }}
                onLoad={() => handleImageLoad(`img:${path}`)}
                onError={() => handleImageError(`img:${path}`)}
              />
              <div className="mt-2">
                Status: {
                  loaded[`img:${path}`] === undefined ? 'Loading...' :
                  loaded[`img:${path}`] ? '✅ Loaded' : '❌ Failed'
                }
              </div>
            </div>
            
            <div className="mt-4">
              <p>Try direct URL access in a new tab: <a href={path} target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">Open image directly</a></p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}