import { NextResponse } from 'next/server';
import { supabase, getImageUrl } from '@/lib/supabase';
import staticImagesData from '@/data/static-images.json';

export async function GET() {
  console.log("[API] GET /api/images-static called");
  
  try {
    // Check if we have the image_metadata table in Supabase
    const { data: tableExistsCheck, error: tableCheckError } = await supabase
      .from('image_metadata')
      .select('count()', { count: 'exact', head: true });
    
    // If the table exists, use it
    if (!tableCheckError && tableExistsCheck) {
      console.log("[API] Using Supabase image_metadata table");
      
      // Fetch images from Supabase instead of filesystem
      const { data: images, error, count } = await supabase
        .from('image_metadata')
        .select('*', { count: 'exact' })
        .limit(3000);
        
      if (error) {
        console.error("[API] Error fetching images:", error.message);
        throw error;
      }
      
      console.log(`[API] Retrieved ${count} images from Supabase`);
      
      // Process images to include full URLs
      const processedImages = images.map(img => {
        // Calculate full URLs for images
        const imagePath = getImageUrl(img.storage_path);
        
        // Calculate composite URL if available
        let compositeUrl = null;
        if (img.has_composite && img.composite_path) {
          compositeUrl = getImageUrl(img.composite_path);
        }
        
        return {
          town: img.town,
          path: imagePath,
          filename: img.filename,
          composite_image: compositeUrl,
          has_composite: img.has_composite
        };
      });
      
      console.log(`[API] Successfully processed ${processedImages.length} images from Supabase`);
      
      // Return processed images
      return NextResponse.json({
        success: true,
        metadata: {
          source: 'supabase',
          total_images: processedImages.length,
          with_composites: processedImages.filter(img => img.has_composite).length
        },
        images: processedImages
      });
    } else {
      // If the table doesn't exist yet or we got an error, fall back to static images
      console.log("[API] Falling back to static images");
      
      const isProduction = process.env.VERCEL || process.env.NODE_ENV === 'production';
      
      // Ensure we have staticImages data
      if (!staticImagesData || !Array.isArray(staticImagesData) || staticImagesData.length === 0) {
        console.error("[API] Static images data is missing or empty!");
        throw new Error("Static images data is missing");
      }
      
      // Process static images for production environment if needed
      let processedImages = staticImagesData;
      if (isProduction) {
        console.log("[API] Adjusting static image paths for production");
        
        processedImages = staticImagesData.map(image => {
          // Extract town and filename from the path
          const pathParts = image.path.split('/');
          const filename = pathParts[pathParts.length - 1];
          const town = image.town.toUpperCase().replace(/ /g, '_');
          
          // Construct the storage path
          const storagePath = `${town}/${filename}`;
          
          // Get full URL from Supabase
          const imagePath = getImageUrl(storagePath);
          
          // Handle composite image if present
          let compositeUrl = null;
          if (image.composite_image && image.has_composite) {
            const compositePathParts = image.composite_image.split('/');
            const compositeFilename = compositePathParts[compositePathParts.length - 1];
            compositeUrl = getImageUrl(`${town}/${compositeFilename}`);
          }
          
          return {
            town: town,
            path: imagePath,
            filename: filename,
            composite_image: compositeUrl || image.composite_image,
            has_composite: image.has_composite
          };
        });
      }
      
      console.log(`[API] Using ${processedImages.length} static images`);
      
      return NextResponse.json({
        success: true,
        metadata: {
          source: 'static-images',
          total_images: processedImages.length,
          with_composites: processedImages.filter(img => img.has_composite).length,
          isProduction: isProduction
        },
        images: processedImages
      });
    }
  } catch (error) {
    console.error("[API] Error processing images:", error);
    
    // Last resort fallback - return sample images
    try {
      console.log("[API] Using emergency fallback with sample images");
      
      // Create a small sample of test images
      const sampleImages = [
        {
          town: "SAMPLE",
          path: "https://quinfer.github.io/flag-examples/union-jack/example1.jpg",
          filename: "sample-union-jack.jpg",
          has_composite: false
        },
        {
          town: "SAMPLE",
          path: "https://quinfer.github.io/flag-examples/ulster-banner/example1.jpg",
          filename: "sample-ulster-banner.jpg",
          has_composite: false
        },
        {
          town: "SAMPLE",
          path: "https://quinfer.github.io/flag-examples/irish-tricolour/example1.jpg",
          filename: "sample-tricolour.jpg",
          has_composite: false
        }
      ];
      
      return NextResponse.json({
        success: true,
        metadata: { 
          source: "emergency-fallback",
          error: error.message,
          total_images: sampleImages.length,
        },
        images: sampleImages
      });
    } catch (fallbackError) {
      console.error("[API] Emergency fallback also failed:", fallbackError);
      return NextResponse.json({
        success: false,
        error: "Failed to load images from all sources",
        images: []
      });
    }
  }
}