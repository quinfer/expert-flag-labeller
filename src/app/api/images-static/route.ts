import { NextResponse } from 'next/server';
import { staticImages } from '@/data/images';

// In-memory storage for classifications
// This will reset when the serverless function cold starts
let classifications = [];

// Initialize with some sample data if needed
try {
  // You can include your initial classifications here
  classifications = [
    {
      "imageId": "masked_o8Pw_udWFAvvose7BnkVOg_120.jpg",
      "town": "MAGHERAFELT",
      "primaryCategory": "National",
      "displayContext": "Pole-mounted",
      "specificFlag": "",
      "confidence": 3,
      "timestamp": "2025-02-25T10:47:54.731Z",
      "expertId": "EX001"
    },
    // Add more initial classifications if needed
  ];
} catch (error) {
  console.error('Error initializing classifications:', error);
}

export async function GET() {
  return NextResponse.json({ images: staticImages, classifications });
}

export async function POST(request) {
  try {
    const data = await request.json();
    
    if (data.action === 'save') {
      // Add new classification
      classifications.push(data.classification);
      return NextResponse.json({ 
        success: true, 
        message: 'Classification saved successfully',
        classificationsCount: classifications.length
      });
    } 
    else if (data.action === 'flag') {
      // Flag an image for review
      const { imageId } = data;
      const existingIndex = classifications.findIndex(c => c.imageId === imageId);
      
      if (existingIndex >= 0) {
        classifications[existingIndex].needsReview = true;
        classifications[existingIndex].reviewReason = data.reason || 'Flagged for review';
      } else {
        classifications.push({
          imageId,
          needsReview: true,
          reviewReason: data.reason || 'Flagged for review',
          timestamp: new Date().toISOString(),
          expertId: data.expertId || 'anonymous'
        });
      }
      
      return NextResponse.json({ 
        success: true, 
        message: 'Image flagged for review'
      });
    }
    else {
      return NextResponse.json({ 
        success: false, 
        error: 'Unknown action' 
      }, { status: 400 });
    }
  } catch (error) {
    console.error('Error processing classification:', error);
    return NextResponse.json({ 
      success: false, 
      error: error.message 
    }, { status: 500 });
  }
}
