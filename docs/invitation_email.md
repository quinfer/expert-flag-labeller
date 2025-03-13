# Expert Flag Labeller: Invitation to Expert Classification Project

Dear Colleagues (Declan, Dominic, Barry, Brandon, and Byron),

I'm writing to invite you to participate in the Expert Flag Labeller project, a specialized web application for the expert classification of flags in Northern Ireland street-level imagery. Your expertise is critical to this academic research project, which aims to develop a comprehensive hierarchical classification system for cultural symbols across Northern Ireland.

## Project Background and Rationale

The Expert Flag Labeller application has been meticulously designed to address the methodological challenges inherent in cultural symbol classification. Our dataset comprises approximately 60,000 flag images collected from 50 towns across Northern Ireland, with each image containing pre-identified potential flags. Through a stratified random sampling approach, we've selected a manageable subset of these images for expert classification.

A key challenge in our methodology has been addressing algorithmic overdetection in street-level imagery. As detailed in our methodology document, many street scenes contain multiple detections—some with upwards of 30 objects in a single image—representing bunting, decorations, and other flag-like items. Our analysis revealed that 37.4% of images contained multiple bounding boxes, with extreme cases having up to 36 detections.

To address this challenge, we've implemented a sophisticated preprocessing algorithm that:
1. Applies adaptive thresholds for detection confidence and relative object size
2. Uses position-aware assessment to handle distant flags that appear smaller in the upper portions of images
3. Provides contextual cropping with appropriate padding to maintain visual context
4. Integrates visual cues to highlight the specific area under consideration

Most significantly, we've now added a side-by-side viewing feature that shows both the cropped flag and its original context in a single image. This provides you with the comprehensive visual information needed for accurate classification while maintaining a focused classification task.

## The Application Interface

The Expert Flag Labeller web application provides a streamlined interface for classification:

1. **Authentication**: Use your personal credentials to securely access the system.
2. **Side-by-Side Image Viewing**: Each classification task presents a side-by-side composite image showing both the cropped flag and its original context for better assessment.
3. **Comprehensive Classification Form**: The hierarchical classification system includes:
   - Primary category (National, Fraternal, Sport, Military, Historical, International, Proscribed)
   - Display context (building-mounted, parade, bunting, etc.)
   - Specific flag identification with detailed subcategories
   - Confidence assessment on a 5-point scale
4. **Review Flagging**: For uncertain cases, you can flag images for additional expert review.
5. **Progress Tracking**: The system maintains your progress, allowing you to resume classification at any time.

## Accessing the Application

The application is now live at [https://expert-flag-labeller.vercel.app/](https://expert-flag-labeller.vercel.app/)

To login:
- **Username**: Your first name (e.g., "Declan", "Dominic", "Barry", "Brandon", or "Byron")
- **Password**: Provided separately for security

## Classification Guidelines

When classifying flags, please:

1. Examine both the cropped flag and its original context in the side-by-side view
2. Select the most appropriate primary category, considering the flag's cultural and political significance
3. Identify the display context, noting whether it appears as an individual flag, bunting, or within a mural
4. Provide specific flag identification where possible
5. Indicate your confidence level on a scale of 1-5
6. Use the "Flag for Review" option only for truly ambiguous cases that require additional expert consultation

## Project Significance

Your expert classifications will serve multiple important purposes:

1. Developing a comprehensive dataset of Northern Ireland flag displays with expert annotations
2. Training machine learning models for automated flag classification using hierarchical prompt tuning
3. Enabling academic research on spatial and temporal patterns of cultural symbol displays
4. Creating a valuable resource for understanding symbolic landscapes in contested environments

This research adheres to strict ethical guidelines, including anonymization of location data, careful handling of sensitive categories, academic usage restrictions, and compliance with data protection regulations.

## Timeline and Support

We request that you complete your classifications within the next four weeks. The application is designed to save your progress automatically, allowing you to work at your convenience.

If you encounter any technical issues or have questions about the classification protocol, please contact me directly at [your-email@example.com](mailto:your-email@example.com).

Thank you for your valuable contribution to this research project. Your domain expertise is essential to creating an accurate classification system for cultural symbols in Northern Ireland.

Sincerely,

Barry Quinn
Project Lead, Expert Flag Labeller