import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const expertId = searchParams.get('expert_id');
    
    if (expertId) {
      // Fetch classifications for specific expert
      const { data: classifications, error } = await supabase
        .from('classifications')
        .select('*')
        .eq('expert_id', expertId)
        .order('timestamp', { ascending: false });
        
      if (error) {
        console.error("Error fetching classifications from Supabase:", error.message);
        return NextResponse.json({ 
          error: error.message,
          classifications: []
        }, { status: 500 });
      }
      
      return NextResponse.json({
        classifications: classifications || [],
        metadata: {
          total_classifications: classifications?.length || 0,
          expert_id: expertId
        }
      });
    } else {
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
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to load data';
    console.error('Error loading data:', error);
    return NextResponse.json({ 
      error: errorMessage,
      images: []
    }, { status: 500 });
  }
}

export async function POST(request: Request) {
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
        review_reason: body.classification.reviewReason ?? null,
        user_content: body.classification.userContent || body.classification.notes || null
      };
      
      console.log('Saving classification to Supabase:', classification);
      
      // Check if this user has already classified this image
      const { data: existingClassifications, error: checkError } = await supabase
        .from('classifications')
        .select('*')
        .eq('expert_id', classification.expert_id)
        .eq('image_id', classification.image_id);
      
      if (checkError) {
        console.error('Error checking existing classifications:', checkError);
        throw new Error(`Check error: ${checkError.message}`);
      }
      
      let responseData = null;
      
      try {
        if (existingClassifications && existingClassifications.length > 0) {
          const existingId = existingClassifications[0].id;
          if (existingClassifications.length > 1) {
            console.warn(
              `Multiple classification rows for same expert+image (${classification.expert_id} / ${classification.image_id}); updating id=${existingId} only`
            );
          }
          const { data, error } = await supabase
            .from('classifications')
            .update(classification)
            .eq('id', existingId)
            .select();
          if (error) {
            console.error('Supabase update error:', error);
            throw new Error(error.message);
          }
          responseData = data;
          console.log('Updated existing classification:', data);
        } else {
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
        }
      } catch (dbError) {
        const dbErrorMessage = dbError instanceof Error ? dbError.message : 'Unknown database error';
        console.error('Database operation failed:', dbError);
        throw new Error(`Database error: ${dbErrorMessage}`);
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
        // Check if THIS EXPERT has already made a decision about this image
        const { data: existingUserRecords, error: fetchError } = await supabase
          .from('classifications')
          .select('*')
          .eq('expert_id', body.expertId || 'anonymous')
          .eq('image_id', body.imageId);
          
        if (fetchError) {
          throw new Error(fetchError.message);
        }
        
        // Get the expert's existing record if it exists
        const existingData = existingUserRecords && existingUserRecords.length > 0 
          ? existingUserRecords[0]
          : null;
          
        console.log(`Found ${existingUserRecords?.length || 0} existing records by this expert for image ${body.imageId}`);
        
        if (existingData) {
          console.log(`Updating existing record by expert ${body.expertId} with ID ${existingData.id}`);
          // Update existing record by this expert
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
          console.log(`Creating new flagged record for expert ${body.expertId} on image ${body.imageId}`);
          // Create new flagged record for this expert
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
        const flagErrorMessage = flagError instanceof Error ? flagError.message : 'Unknown flag error';
        console.error('Error flagging for review:', flagError);
        throw new Error(`Flag error: ${flagErrorMessage}`);
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
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    const errorDetails = {
      message: errorMessage,
      stack: error instanceof Error ? error.stack : undefined,
      name: error instanceof Error ? error.name : 'Unknown'
    };
    
    console.error('Error details:', errorDetails);
    
    return NextResponse.json({ 
      success: false, 
      error: errorMessage,
      details: process.env.NODE_ENV === 'development' ? errorDetails : undefined
    }, { status: 500 });
  }
}