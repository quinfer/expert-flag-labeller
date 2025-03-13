'use client';

import { useState, useEffect } from 'react';
import { staticImages } from '../../data/static-images';

export default function StaticTestPage() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showPaths, setShowPaths] = useState(false);
  
  // Get the current image safely
  const currentImage = staticImages && staticImages.length > 0 && currentIndex < staticImages.length 
    ? staticImages[currentIndex] 
    : null;
  
  const handleNext = () => {
    if (currentIndex < staticImages.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };
  
  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };
  
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Static Images Test Page</h1>
      
      <div className="flex justify-between mb-4">
        <div>
          Image {currentIndex + 1} of {staticImages.length}
        </div>
        <div>
          <button 
            className="bg-gray-200 px-3 py-1 rounded mr-2"
            onClick={() => setShowPaths(!showPaths)}
          >
            {showPaths ? 'Hide Paths' : 'Show Paths'}
          </button>
        </div>
      </div>
      
      {currentImage ? (
        <div className="border p-4 rounded">
          <div className="mb-2 font-semibold">
            Town: {currentImage.town}
          </div>
          
          {showPaths && (
            <div className="mb-4 p-2 bg-gray-100 rounded overflow-x-auto">
              <div>Path: {currentImage.path}</div>
              <div>Filename: {currentImage.filename}</div>
            </div>
          )}
          
          <div className="mb-4 flex justify-center">
            <img 
              src={currentImage.path}
              alt={`Flag in ${currentImage.town}`}
              style={{ maxWidth: '100%', maxHeight: '400px' }}
              onError={(e) => {
                console.error("Failed to load image:", currentImage.path);
                e.currentTarget.src = '/placeholder';
              }}
            />
          </div>
          
          <div className="mt-4 flex justify-between">
            <button 
              className="bg-blue-500 text-white px-4 py-2 rounded"
              onClick={handlePrevious}
              disabled={currentIndex === 0}
            >
              Previous
            </button>
            
            <button 
              className="bg-blue-500 text-white px-4 py-2 rounded"
              onClick={handleNext}
              disabled={currentIndex === staticImages.length - 1}
            >
              Next
            </button>
          </div>
        </div>
      ) : (
        <div className="text-center p-4 border rounded">
          <p className="text-red-500">No images available</p>
        </div>
      )}
    </div>
  );
}