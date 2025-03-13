'use client';

interface DirectImageProps {
  path: string;
  town: string;
  filename: string;
}

export default function DirectImage({ path, town, filename }: DirectImageProps) {
  // Create multiple potential paths to try
  const possiblePaths = [
    path,
    path.startsWith('/') ? path.substring(1) : `/${path}`,
    `/images/${town}/${filename}`,
    `images/${town}/${filename}`,
    `/static/${town}/${filename}`,  // New static path
    `static/${town}/${filename}`,   // New static path without leading slash
    `/public/images/${town}/${filename}`,
    `public/images/${town}/${filename}`,
    `${filename}`
  ];
  
  return (
    <div>
      <h3 className="text-sm font-semibold mb-2">Testing multiple paths:</h3>
      
      <div className="space-y-4">
        {possiblePaths.map((testPath, index) => (
          <div key={index} className="border p-2 rounded">
            <div className="text-xs mb-2 bg-gray-100 p-1">{testPath}</div>
            <img 
              src={testPath} 
              alt={`Path ${index+1}`}
              style={{ maxWidth: '100%', height: 'auto', marginTop: '4px' }}
              onLoad={() => console.log(`SUCCESS: Image loaded with path: ${testPath}`)}
              onError={() => console.log(`FAILED: Image failed to load with path: ${testPath}`)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}