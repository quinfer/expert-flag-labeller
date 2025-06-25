# Supabase Setup Guide

This guide walks through setting up Supabase for the Expert Flag Labeler application.

## Prerequisites

- Access to the Supabase project dashboard
- Admin credentials for database access
- Local environment set up with Node.js

## Environment Variables

Add these variables to your `.env.local` file (for local development) and to your Vercel environment variables (for production):

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-public-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
NEXT_PUBLIC_STORAGE_BUCKET=flag-images
```

## Database Setup

1. **Create Image Metadata Table**

   Navigate to the SQL Editor in your Supabase dashboard and run:
   
   ```sql
   -- Use the script in scripts/setup-image-metadata.sql
   ```
   
   This creates a table to store image metadata including paths to the images in Storage.

2. **Enable Row Level Security**

   Apply RLS policies to secure your data:
   
   ```sql
   -- Use the script in scripts/setup-image-metadata-rls.sql
   ```

## Storage Bucket Setup

1. Navigate to the "Storage" section in your Supabase dashboard
2. Click "Create new bucket"
3. Name it `flag-images` (must match NEXT_PUBLIC_STORAGE_BUCKET in your env vars)
4. Enable public access for the bucket (so images can be viewed without authentication)

## Upload Images

1. Ensure your `.env.local` file has the correct Supabase credentials
2. Run the upload script:

   ```bash
   node scripts/upload-images-to-supabase.js
   ```

3. After images are uploaded, populate the metadata:

   ```bash
   node scripts/populate-image-metadata.js
   ```

## Verifying Setup

1. Check the Storage browser in Supabase to confirm images were uploaded
2. Run a query to verify metadata was inserted:

   ```sql
   SELECT COUNT(*) FROM image_metadata;
   ```

3. Start your Next.js application and verify images load correctly

## Troubleshooting

- If images don't appear, check browser console for URL errors
- Ensure your storage bucket is set to public
- Verify the paths in image_metadata match the actual paths in storage