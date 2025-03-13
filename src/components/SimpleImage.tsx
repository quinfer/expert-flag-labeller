'use client';

interface SimpleImageProps {
  src: string;
  alt?: string;
  className?: string;
}

export default function SimpleImage({ src, alt = "Image", className = "" }: SimpleImageProps) {
  return (
    <div className={`simple-image-container ${className}`}>
      <div className="debug" style={{ 
        fontSize: '10px', 
        backgroundColor: '#eee', 
        padding: '4px', 
        marginBottom: '5px'
      }}>
        Loading image from: {src}
      </div>
      <img
        src={src}
        alt={alt}
        style={{
          maxWidth: '100%',
          height: 'auto',
          border: '1px solid #ddd'
        }}
      />
    </div>
  );
}