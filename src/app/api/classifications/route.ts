import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export async function GET() {
  const { data, error } = await supabase
    .from('classifications')
    .select('*')
    .order('timestamp', { ascending: false });
    
  if (error) {
    console.error('Error fetching classifications:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  
  return NextResponse.json({ classifications: data });
}

export async function POST(request) {
  try {
    const body = await request.json();
    
    if (body.action === 'save') {
      // Convert camelCase to snake_case for database
      const classification = {
        image_id: body.classification.imageId,
        town: body.classification.town,
        primary_category: body.classification.primaryCategory,
        display_context: body.classification.displayContext,
        specific_flag: body.classification.specificFlag,
        confidence: body.classification.confidence,
        expert_id: body.classification.expertId || 'anonymous',
        user_context: body.classification.userContext,
        needs_review: body.classification.needsReview || false,
        review_reason: body.classification.reviewReason
      };
      
      const { data, error } = await supabase
        .from('classifications')
        .insert([classification])
        .select();
        
      if (error) {
        throw new Error(error.message);
      }
      
      return NextResponse.json({ 
        success: true, 
        message: 'Classification saved successfully',
        data
      });
    } 
    else if (body.action === 'flag') {
      const { data: existingData, error: fetchError } = await supabase
        .from('classifications')
        .select('*')
        .eq('image_id', body.imageId)
        .maybeSingle();
        
      if (fetchError) {
        throw new Error(fetchError.message);
      }
      
      if (existingData) {
        // Update existing record
        const { error: updateError } = await supabase
          .from('classifications')
          .update({ 
            needs_review: true,
            review_reason: body.reason || 'Flagged for review'
          })
          .eq('id', existingData.id);
          
        if (updateError) {
          throw new Error(updateError.message);
        }
      } else {
        // Create new record
        const { error: insertError } = await supabase
          .from('classifications')
          .insert([{
            image_id: body.imageId,
            needs_review: true,
            review_reason: body.reason || 'Flagged for review',
            expert_id: body.expertId || 'anonymous',
            primary_category: 'Review'
          }]);
          
        if (insertError) {
          throw new Error(insertError.message);
        }
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
