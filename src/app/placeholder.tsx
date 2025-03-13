'use client';

import { NextResponse } from 'next/server';

// A simple component that renders a placeholder image
export default function Placeholder() {
  return (
    <svg 
      width="200" 
      height="150" 
      viewBox="0 0 200 150" 
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="200" height="150" fill="#f8f8f8" />
      <text 
        x="100" 
        y="75" 
        fontFamily="Arial" 
        fontSize="14" 
        textAnchor="middle" 
        fill="#666"
      >
        Image not found
      </text>
    </svg>
  );
}

// API route to serve the placeholder as an image
export async function GET() {
  const svg = `<svg 
    width="200" 
    height="150" 
    viewBox="0 0 200 150" 
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect width="200" height="150" fill="#f8f8f8" />
    <text 
      x="100" 
      y="75" 
      fontFamily="Arial" 
      fontSize="14" 
      textAnchor="middle" 
      fill="#666"
    >
      Image not found
    </text>
  </svg>`;
  
  return new NextResponse(svg, {
    headers: {
      'Content-Type': 'image/svg+xml',
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  });
}