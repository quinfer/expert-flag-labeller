import { NextResponse } from 'next/server';
import staticImages from '@/data/static-images.json';
import expertConfirmedData from '@/data/expert-confirmed-detailed.json';

export async function GET() {
  // Apply expert-confirmed curation instead of false positive filtering
  const curatedImages = applyExpertConfirmedCuration(staticImages);
  
  return NextResponse.json({ 
    success: true, 
    images: curatedImages,
    metadata: {
      curation: 'expert-confirmed',
      total_images: curatedImages.length,
      curation_stats: {
        original_count: staticImages.length,
        curated_count: curatedImages.length,
        curation_rate: ((curatedImages.length / staticImages.length) * 100).toFixed(1) + '%'
      }
    }
  });
}

/**
 * Apply expert-confirmed curation to filter images
 * Only returns images that have been verified by experts as containing flags
 */
function applyExpertConfirmedCuration(images: any[]): any[] {
  try {
    // Create a set of expert-confirmed image IDs for fast lookup
    const expertConfirmedSet = new Set(Object.keys(expertConfirmedData));
    
    // Filter images to only include expert-confirmed ones
    const curatedImages = images.filter(image => {
      // Extract the image ID from the filename (handle _box0 suffix)
      const imageId = image.filename.replace('_box0.jpg', '.jpg');
      return expertConfirmedSet.has(imageId);
    });
    
    console.log(`[CURATION] Filtered ${images.length} images to ${curatedImages.length} expert-confirmed images`);
    
    return curatedImages;
  } catch (error) {
    console.error("[CURATION] Error applying expert-confirmed curation:", error);
    // If curation fails, return all images as fallback
    return images;
  }
}
