# Expert Flag Labeller: Complete User Guide

## Welcome to the Expert Flag Labeller Project

Welcome to the Expert Flag Labeller project, a specialized web application for the expert classification of flags in Northern Ireland street-level imagery. Your expertise is invaluable to this academic research project, which aims to develop a comprehensive hierarchical classification system for cultural symbols across Northern Ireland.

## Project Background

The Expert Flag Labeller application addresses methodological challenges in cultural symbol classification through advanced image processing and expert labeling. Our dataset comprises approximately 60,000 flag images collected from 50 towns across Northern Ireland, with each image containing pre-identified potential flags.

Through stratified random sampling, we've selected a manageable subset of these images for expert classification. This sampling ensures balanced representation across:

- Geographical distribution (all towns)
- Varying detection complexity (single vs. multi-flag images)
- Different environmental contexts
- Various display types and conditions

### The Side-by-Side Viewing Solution

A significant advancement in our methodology is the implementation of side-by-side viewing. Each classification task presents both:

1. **The cropped flag (left side)** - For detailed flag examination
2. **The original context (right side)** - To understand the flag's placement and surroundings

This approach provides you with comprehensive visual information while maintaining a focused classification task.

## Getting Started

### Accessing the Application

The application is live at: **https://expert-flag-labeller-production.up.railway.app**

### Your Login Credentials

- **Username:** `May`
- **Password:** `mK9nP2xW7vQ4jL8+`

*Please keep these credentials secure and do not share them with others.*

## Application Interface Overview

The Expert Flag Labeller web application provides an intuitive interface for classification:

1. **Secure Authentication**: Log in with your personal credentials
2. **Side-by-Side Image Viewing**: Each task shows both the flag detail and its original context
3. **Comprehensive Classification Form**: Detailed options for accurate categorization
4. **Review Flagging**: Mark uncertain cases for additional expert review
5. **Progress Tracking**: Resume classification at any time with saved progress

## Complete Classification Instructions

### Step-by-Step Classification Process

Your task is to classify the bounded flag in each Google Street View image by following these steps:

1. **Select a Primary Category** - Choose the most appropriate category for the flag shown in the image.

2. **Select Display Context** - From the dropdown menu, select where and how the flag is being displayed.

3. **Select Specific Flag** - If applicable, choose the specific flag type from the dropdown options.

4. **Rate Your Confidence** - Use the slider to indicate how confident you are in your classification (1-5 scale):
   - 1 = Very uncertain
   - 2 = Somewhat uncertain
   - 3 = Moderately confident
   - 4 = Quite confident
   - 5 = Very confident

5. **Save & Continue** - Click the "Save & Next" button to submit your classification and move to the next image.

### Classification Guidelines

When classifying flags, please:

1. **Examine both views**: Look at both the cropped flag and its original context
2. **Select the primary category**: Choose the most appropriate academic category
3. **Identify the display context**: Note how the flag is presented (individual, bunting, mural, etc.)
4. **Provide specific identification**: Select the specific flag type where possible
5. **Indicate confidence**: Use the 1-5 scale to indicate your certainty
6. **Flag for review**: Use this option only for truly ambiguous cases

### Primary Categories Available

The system includes several primary categories for flag classification:

- **National**: National flags and official state symbols
- **Fraternal**: Flags associated with organizations and societies
- **Sport**: Sports team and club flags
- **Military**: Military and regimental flags
- **Historical**: Historical flags and commemorative displays
- **International**: International organization flags
- **Proscribed**: Flags associated with proscribed organizations

### Display Context Options

You'll be able to select from various display contexts including:

- Individual flag displays
- Building-mounted flags
- Parade displays
- Bunting arrangements
- Mural displays
- And other contextual settings

## Flagging Images for Review

If you encounter an image with issues, click the "Flag for Review" button. You can select from these reasons:

- **Not a flag** - The image shows a decoration or other non-flag item (note: bunting should be classified, not flagged)
- **Unclear image** - The image is too blurry, dark, or otherwise difficult to classify
- **Complex case** - The image requires additional expert review
- **Other reason** - Any other issue not covered by the options above

## Navigation and Progress Management

### Navigation Controls
- Use the **"Previous Image"** and **"Save & Next"** buttons to navigate between images
- The interface will track your progress automatically

### Saving Your Progress
- **Automatic saving**: Your progress is automatically saved when you logout, allowing you to return exactly where you left off when you log back in
- **Manual saving**: You can also use the "Save Progress" button at any time to manually save your current position without logging out
- This is useful for marking important points in your classification work

### Progress Statistics
The interface provides real-time statistics showing:
- Number of images classified
- Images flagged for review
- Your average confidence level
- Overall progress through the dataset

## Understanding the Dataset

### Image Quality and Preprocessing

The images you'll be classifying have been preprocessed using advanced algorithms to ensure optimal viewing:

- **Quality assurance**: All images are expert-confirmed to contain flags
- **Context preservation**: Both detailed and contextual views are provided
- **Intelligent filtering**: Algorithmic overdetection has been filtered to present only relevant flags
- **Position-aware processing**: Images are cropped and processed to highlight the flag of interest

### Expected Image Types

You may encounter various types of flag displays:

- Single flags on buildings
- Multiple flags in the same scene
- Bunting and decorative arrangements
- Flags in parade or ceremonial contexts
- Historical or commemorative displays

## Project Significance

Your expert classifications will contribute to:

1. **Creating a validated dataset** of Northern Ireland flag displays
2. **Training machine learning models** for automated flag classification
3. **Supporting academic research** on spatial and temporal patterns of cultural symbol displays
4. **Developing a valuable resource** for understanding symbolic landscapes

This research adheres to strict ethical guidelines, including anonymization of location data, careful handling of sensitive categories, and compliance with data protection regulations.

## Technical Tips and Best Practices

### For Optimal Classification Experience:
- Use a larger screen when possible for better image detail
- Take breaks regularly to maintain classification accuracy
- Don't rush - accuracy is more important than speed
- When in doubt, use the "Flag for Review" option rather than guessing

### If You Experience Technical Issues:
- Try refreshing the browser page
- Clear your browser cache if images don't load properly
- Ensure you have a stable internet connection
- Contact support if issues persist

## Timeline and Support

We request that you complete your classifications within the next four weeks. The application saves your progress automatically, allowing you to work at your convenience.

### Contact Information
For technical issues or questions about the classification protocol, please contact:

**Barry Quinn**  
Project Lead, Expert Flag Labeler  
[Contact details to be provided separately]

## Research Ethics and Data Handling

This research project follows strict ethical guidelines:

- All location data is anonymized
- Sensitive categories are handled with appropriate care
- Full compliance with data protection regulations
- Expert classifications are stored securely
- No personal information is associated with classifications

## Acknowledgments

Thank you for your valuable contribution to this research project. Your expertise is essential to creating an accurate classification system for cultural symbols in Northern Ireland. Your careful work will contribute to academic understanding and the development of advanced machine learning systems for cultural symbol analysis.

---

**Document Version:** 1.0  
**Last Updated:** July 2025
**Application URL:** https://expert-flag-labeller-production.up.railway.app 