import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Helper to get image URL from Supabase Storage
export const getImageUrl = (path: string): string => {
  const bucketName = process.env.NEXT_PUBLIC_STORAGE_BUCKET || 'flag-images';
  
  // If path already includes the bucket name, don't add it again
  if (path.includes(`${bucketName}/`)) {
    return `${supabaseUrl}/storage/v1/object/public/${path}`;
  }
  
  return `${supabaseUrl}/storage/v1/object/public/${bucketName}/${path}`;
};

// Helper to get town-specific image path
export const getTownImagePath = (town: string, filename: string): string => {
  const formattedTown = town.replace(/ /g, '_').toUpperCase();
  return `${formattedTown}/${filename}`;
};