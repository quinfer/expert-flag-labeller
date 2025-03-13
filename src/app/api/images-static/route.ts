import { NextResponse } from 'next/server';
import { staticImages } from '@/data/images';
import fs from 'fs';
import path from 'path';

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

// Path to the classification queue JSON file
const QUEUE_FILE = path.join(process.cwd(), 'data', 'classification_queue.json');

export async function GET() {
  console.log("[API] GET /api/images-static called");
  
  try {
    // Check if we should include side-by-side composite images
    let imagesWithComposites = [...staticImages];
    
    // Check if we're in production environment (e.g., Vercel)
    const isProduction = process.env.VERCEL || process.env.NODE_ENV === 'production';
    console.log(`[API] Running in ${isProduction ? 'production' : 'development'} mode`);
    
    // Attempt to read the classification queue to find composite images
    // This will likely fail in production since the file is excluded from deployment
    let queueDataLoaded = false;
    
    if (!isProduction && fs.existsSync(QUEUE_FILE)) {
      console.log("[API] Classification queue file found, checking for composite images");
      try {
        const queueData = JSON.parse(fs.readFileSync(QUEUE_FILE, 'utf8'));
        
        if (queueData && queueData.images && queueData.images.length > 0) {
          console.log(`[API] Found ${queueData.images.length} images in classification queue`);
          queueDataLoaded = true;
          
          // Create a lookup map by filename
          const queueMap = new Map();
          queueData.images.forEach(item => {
            queueMap.set(item.filename, item);
          });
          
          console.log("[API] First few queue items:", queueData.images.slice(0, 2));
          console.log("[API] First few static images:", staticImages.slice(0, 2));
          
          // Enhance staticImages with composite image information
          imagesWithComposites = imagesWithComposites.map(image => {
            const queueItem = queueMap.get(image.filename);
            if (queueItem && queueItem.composite_image) {
              console.log(`[API] Match found for ${image.filename}, adding composite ${queueItem.composite_image}`);
              return {
                ...image,
                composite_image: queueItem.composite_image,
                has_composite: true
              };
            }
            return image;
          });
          
          console.log(`[API] Enhanced ${imagesWithComposites.filter(img => img.has_composite).length} images with composite data`);
          
          // Log a sample of images with composites
          const compositeSamples = imagesWithComposites.filter(img => img.has_composite).slice(0, 2);
          if (compositeSamples.length > 0) {
            console.log("[API] Sample composite image data:", compositeSamples);
          } else {
            console.log("[API] No composite images were found in the enhanced list");
          }
        }
      } catch (error) {
        console.error("[API] Error reading queue file:", error);
      }
    } else {
      console.log("[API] Classification queue file not found or running in production mode");
    }
    
    // For production, add a fake composite flag on the first few images for demo purposes
    if (isProduction) {
      console.log("[API] Adding mock composite image data for production demo");
      imagesWithComposites = imagesWithComposites.map((image, index) => {
        // Add composite flag to first 10 images
        if (index < 10) {
          return {
            ...image,
            has_composite: true,
            composite_image: image.path.replace('.jpg', '_composite.jpg'),
            is_production_mock: true
          };
        }
        return image;
      });
    }
    
    if (!imagesWithComposites || imagesWithComposites.length === 0) {
      console.error("[API] CRITICAL ERROR: images array is empty in API route!");
    } else {
      console.log("[API] First image in response:", imagesWithComposites[0]);
    }
    
    // Return enhanced images with composite information
    return NextResponse.json({
      success: true,
      metadata: { 
        source: queueDataLoaded ? "static-images-with-composites" : "static-images-only",
        totalImages: imagesWithComposites.length,
        compositesCount: imagesWithComposites.filter(img => img.has_composite).length,
        inProduction: isProduction,
        note: isProduction ? "Running in production. Actual image files are not available." : ""
      },
      images: imagesWithComposites || [],
      classifications: classifications || []
    });
  } catch (error) {
    console.error("[API] Error processing images:", error);
    
    // Fallback to returning static images directly
    return NextResponse.json({
      success: true,
      metadata: { 
        source: "static-images-direct-fallback",
        error: error.message
      },
      images: staticImages || []
    });
  }
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
