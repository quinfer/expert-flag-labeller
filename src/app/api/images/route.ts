import { NextResponse } from 'next/server';
import { staticImages } from '@/data/images';

export async function GET() {
  return NextResponse.json({ 
    success: true, 
    images: staticImages 
  });
}
