# Deployment Instructions

This guide provides a comprehensive walkthrough for deploying the Expert Flag Labeler application with processed imagery. The instructions cover all aspects from image preparation to final deployment.

## System Architecture Overview

The Expert Flag Labeler application consists of:

1. **Image Processing Pipeline**: Python scripts that prepare and optimize flag images
2. **Static Image Storage**: Processed images stored in the `/public` directory
3. **Web Application**: A Next.js application for experts to classify flag images
4. **Database**: Supabase database for storing classifications

## Prerequisites

Before beginning deployment, ensure you have:

- Python 3.6+ installed (for image processing)
- Node.js 14+ installed (for web application)
- Access to the GitHub repository
- Vercel account (for hosting)
- Supabase account (for database)
- At least 10GB of disk space for image processing

## Deployment Process

### 1. Prepare the Environment

First, set up your local environment:

```bash
# Clone the repository
git clone https://github.com/your-username/expert-flag-labeler.git
cd expert-flag-labeler

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
```

Edit `.env.local` to include your Supabase credentials:

```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 2. Process Images for Classification

This step converts raw flag images into classification-ready formats:

```bash
# Basic processing with recommended settings
python scripts/prepare_images_for_classification.py \
  --side-by-side \
  --min-confidence 0.3 \
  --min-size 0.005 \
  --copy-to-public
```

**Key Parameters Explained:**
- `--side-by-side`: Creates composite views showing both the cropped flag and its context
- `--min-confidence 0.3`: Only includes detections with at least 30% confidence
- `--min-size 0.005`: Only includes objects that are at least 0.5% of the image area
- `--copy-to-public`: Copies processed images to the public directory

**What Happens:**
- The script processes all town folders in `data/true_positive_images`
- It creates cropped images focused on each bounding box
- It generates side-by-side composite views
- All processed images are saved to `data/cropped_images_for_classification`
- Images are copied to `public/images/{TOWN}` directories
- A classification queue is generated at `data/classification_queue.json`

### 3. Prepare Web Application Image Resources

Generate the necessary files for the web application to access images:

```bash
# Generate the image list for the application
node scripts/generate-image-list.js

# Copy images to static directory for reliable serving
node scripts/copy-images-to-static.js
```

These scripts:
- Create `src/data/images.json` and `src/data/images.js` listing all available images
- Set up `public/static/{TOWN}` directories with optimized images
- Generate `src/data/static-images.js` and `src/data/static-images.json`

### 4. Verify Image Processing

Check that the images are properly processed:

```bash
# Verify composite images exist
node scripts/verify-composite-images.js

# Check image counts
python -c "import json; f=open('data/classification_queue.json'); data=json.load(f); print(f\"Total images: {data['metadata']['total_images']}\")"
```

### 5. Configure Supabase Database

Set up your Supabase database for storing classifications:

1. Create a new Supabase project at [https://supabase.com](https://supabase.com)
2. Set up the classifications table:

```sql
CREATE TABLE classifications (
  id SERIAL PRIMARY KEY,
  image_path TEXT NOT NULL,
  town TEXT NOT NULL,
  primary_category TEXT NOT NULL,
  specific_type TEXT,
  display_context TEXT,
  confidence INTEGER,
  user_email TEXT,
  user_name TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

3. Set up row-level security (RLS) policies for secure access
4. Update your `.env.local` file with the database credentials

### 6. Test Locally

Before deployment, test the application locally:

```bash
# Start the development server
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) and verify:
- Images load correctly with side-by-side views
- Classification form works
- Data is saved to Supabase

### 7. Deploy to Vercel

Deploy the application to Vercel:

```bash
# Install Vercel CLI if not already installed
npm install -g vercel

# Deploy to Vercel
vercel deploy
```

Follow the prompts to connect to your Vercel account and deploy the application.

**Important Deployment Considerations:**

1. Configure environment variables in the Vercel dashboard
2. Set appropriate resource limits for the deployment
3. If image assets are large, consider using Vercel's Large Static Assets support
4. Ensure authentication is properly configured for expert access

### 8. Post-Deployment Verification

After deployment:

1. Test image loading on the production site
2. Verify authentication works
3. Test classification submission
4. Check that classifications are saved to Supabase

## Maintenance and Updates

To update the app with new images:

1. Run the preprocessing script with the latest dataset
2. Run the image list and static copy scripts
3. Redeploy to Vercel

The app's code can be updated independently from the image processing pipeline.

## Troubleshooting Deployment Issues

### Common Issues and Solutions

#### "Large File Size" Warning During Deployment

If Vercel warns about large static files:

1. Reduce the sample size of images
2. Consider using a separate CDN for images
3. Use a smaller subset for initial deployment

#### Performance Issues with Many Images

If the application is slow:

1. Optimize image loading with smaller static sets
2. Implement pagination for image classification
3. Consider server-side rendering for image pages

#### Authentication Problems

If users can't log in:

1. Verify authentication environment variables
2. Check Supabase authentication settings
3. Test with multiple browsers

## Expert Onboarding

After deployment, invite experts to use the system:

1. Provide the application URL
2. Share login credentials individually
3. Offer the [Invitation Email](./invitation_email.md) with detailed instructions
4. Consider a brief training session for first-time users

## Glossary

- **Bounding Box**: A rectangular outline that indicates the position of a detected flag
- **Confidence Score**: A value (0-100%) indicating the detection algorithm's certainty
- **Cropped Image**: A portion of a larger image focused on a specific flag
- **Composite Image**: A side-by-side view showing both the cropped flag and its original context
- **Multi-Box Image**: An image containing multiple detected flags
- **Classification Queue**: The list of images ready for expert labeling