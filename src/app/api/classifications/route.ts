import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export async function GET() {
  try {
    // Fetch images from Supabase instead of filesystem
    const { data: images, error, count } = await supabase
      .from('image_metadata')
      .select('*', { count: 'exact' })
      .limit(3000);
      
    if (error) {
      console.error("Error fetching images from Supabase:", error.message);
      return NextResponse.json({ 
        error: error.message,
        images: []
      }, { status: 500 });
    }
    
    // Return the images array
    return NextResponse.json({
      images: images || [],
      metadata: {
        total_images: count || images?.length || 0
      }
    });
  } catch (error) {
    console.error('Error loading images:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to load images',
      images: []
    }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    console.log('Received POST body:', JSON.stringify(body, null, 2));
    
    if (body.action === 'save') {
      // Map to actual column names from Supabase response
      const classification = {
        image_id: body.classification.imageId,
        town: body.classification.town,
        primary_category: body.classification.primaryCategory,
        display_context: body.classification.displayContext,
        specific_flag: body.classification.specificFlag,
        confidence: body.classification.confidence,
        expert_id: body.classification.expertId || 'anonymous',
        needs_review: body.classification.needsReview || false,
        review_reason: body.classification.reviewReason,
        user_content: body.classification.userContent || body.classification.notes
      };
      
      console.log('Saving classification to Supabase:', classification);
      
      let responseData = null;
      
      try {
        const { data, error } = await supabase
          .from('classifications')
          .insert([classification])
          .select();
          
        if (error) {
          console.error('Supabase insert error:', error);
          throw new Error(error.message);
        }
        
        responseData = data;
        console.log('Successfully saved classification:', data);
      } catch (dbError) {
        console.error('Database operation failed:', dbError);
        throw new Error(`Database error: ${dbError.message}`);
      }
      
      return NextResponse.json({ 
        success: true, 
        message: 'Classification saved successfully',
        data: responseData
      });
    } 
    else if (body.action === 'flag') {
      let flagResult = null;
      
      try {
        // First get all matching rows
        const { data: allMatches, error: fetchError } = await supabase
          .from('classifications')
          .select('*')
          .eq('image_id', body.imageId);
          
        if (fetchError) {
          throw new Error(fetchError.message);
        }
        
        // Get the most recent record if multiple exist
        const existingData = allMatches && allMatches.length > 0 
          ? allMatches.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0]
          : null;
          
        console.log(`Found ${allMatches?.length || 0} matches for image ${body.imageId}`);
        
        if (existingData) {
          console.log(`Updating existing record with ID ${existingData.id}`);
          // Update existing record
          const { data: updateData, error: updateError } = await supabase
            .from('classifications')
            .update({ 
              needs_review: true,
              review_reason: body.reason || 'Flagged for review'
            })
            .eq('id', existingData.id)
            .select();
            
          if (updateError) {
            throw new Error(updateError.message);
          }
          
          flagResult = updateData;
        } else {
          console.log(`Creating new record for flagged image ${body.imageId}`);
          // Create new record
          const { data: insertData, error: insertError } = await supabase
            .from('classifications')
            .insert([{
              image_id: body.imageId,
              needs_review: true,
              review_reason: body.reason || 'Flagged for review',
              expert_id: body.expertId || 'anonymous',
              primary_category: 'Review',
              town: body.town || 'Unknown'
            }])
            .select();
            
          if (insertError) {
            throw new Error(insertError.message);
          }
          
          flagResult = insertData;
        }
        
        console.log('Successfully flagged for review:', flagResult);
      } catch (flagError) {
        console.error('Error flagging for review:', flagError);
        throw new Error(`Flag error: ${flagError.message}`);
      }
      
      return NextResponse.json({ 
        success: true, 
        message: 'Image flagged for review',
        data: flagResult
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
    
    // Create a more detailed error message for debugging
    const errorDetails = {
      message: error.message,
      stack: error.stack,
      name: error.name
    };
    
    console.error('Error details:', errorDetails);
    
    return NextResponse.json({ 
      success: false, 
      error: error.message,
      details: process.env.NODE_ENV === 'development' ? errorDetails : undefined
    }, { status: 500 });
  }
}