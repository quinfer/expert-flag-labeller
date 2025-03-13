'use client'

import { useState, useEffect } from 'react'
import { useRouter } from "next/navigation"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import Image from 'next/image'
import { Info, HelpCircle } from 'lucide-react'
import { InstructionsModal } from '@/components/InstructionsModal'
import FlagClassificationForm from '@/components/FlagClassificationForm'
import BoundedFlagImage from '@/components/BoundedFlagImage'
import SimpleCompositeImage from '@/components/SimpleCompositeImage'
// Import images from static-images.js if it exists, otherwise fall back to regular images
import { staticImages as originalImages } from '../data/images'
import { staticImages as staticImagesAlternate } from '../data/static-images'

// Use the static images if available, otherwise fall back to the original images
const staticImages = staticImagesAlternate.length > 0 ? staticImagesAlternate : originalImages;

interface ImageData {
  town: string;
  path: string;
  filename: string;
}

// Add type for flagCategories
type FlagCategory = {
  primary: string;
  context: string;
}

type FlagCategories = {
  [key: string]: FlagCategory;
}

// Example classification schema
interface Classification {
  imageId: string
  town: string
  primaryCategory: string
  specificFlag: string
  displayContext: string
  userContext: string
  confidence: number
  timestamp: string
  expertId: string  // This will store the username of the expert
  // ... other fields
}

// Flag reference examples - using the correct paths
const flagExamples = {
  'European Union' : ['https://quinfer.github.io/flag-examples/eu/example1.jpg'],
  'Scottish Saltire' : ['https://quinfer.github.io/flag-examples/scottish-saltire/example1.jpg'],
  'Apprentice Boys': ['https://quinfer.github.io/flag-examples/apprentice-boys/example1.jpg',
                      'https://quinfer.github.io/flag-examples/apprentice-boys/example2.jpg'
  ],
  'Union Jack': ['https://quinfer.github.io/flag-examples/union-jack/example1.jpg'],
  'Ulster Banner': ['https://quinfer.github.io/flag-examples/ulster-banner/example1.jpg'],
  'Irish Tricolor': ['https://quinfer.github.io/flag-examples/irish-tricolour/example1.jpg'],
  'Orange Order': ['https://quinfer.github.io/flag-examples/orange-order/example1.jpg',
                   'https://quinfer.github.io/flag-examples/orange-order/example2.jpg',
                   'https://quinfer.github.io/flag-examples/orange-order/example3.jpg',
                   'https://quinfer.github.io/flag-examples/orange-order/example4.jpg'
  ],
  'Parachute Regiment': ['https://quinfer.github.io/flag-examples/paras/example1.jpg'],
  'Royal Standard': ['https://quinfer.github.io/flag-examples/royal-std/example1.jpg'],
  'Northern Ireland Football': ['https://quinfer.github.io/flag-examples/ni-football/example1.jpg'],
  'UVF': ['https://quinfer.github.io/flag-examples/uvf/example1.jpg'],
  'UDA': ['https://quinfer.github.io/flag-examples/uda/example1.jpg'],
  'UDR': ['https://quinfer.github.io/flag-examples/udr/example1.jpg',
          'https://quinfer.github.io/flag-examples/udr/example2.jpg',
          'https://quinfer.github.io/flag-examples/udr/example3.jpg',
  ],
  'UFF': ['https://quinfer.github.io/flag-examples/uff/example1.jpg'],
  'YCV': ['https://quinfer.github.io/flag-examples/ycv/example1.jpg',
          'https://quinfer.github.io/flag-examples/ycv/example2.jpg',
          'https://quinfer.github.io/flag-examples/ycv/example3.jpg'
  ],
  'WW1 Commemorative': ['https://quinfer.github.io/flag-examples/ww1/example1.jpg',
                        'https://quinfer.github.io/flag-examples/ww1/example2.jpg',
                        'https://quinfer.github.io/flag-examples/ww1/example3.jpg',
                        'https://quinfer.github.io/flag-examples/ww1/example4.jpg'
],
  'Israeli': ['https://quinfer.github.io/flag-examples/isreal/example1.jpg'],
  'Palestinian' : ['https://quinfer.github.io/flag-examples/palestine/example1.jpg'],
  'GAA' : ['https://quinfer.github.io/flag-examples/gaa/example1.jpg',
           'https://quinfer.github.io/flag-examples/gaa/example2.jpg',
           'https://quinfer.github.io/flag-examples/gaa/example3.jpg',
           'https://quinfer.github.io/flag-examples/gaa/example4.jpg'
],
  'Red Hand Defenders' : ['https://quinfer.github.io/flag-examples/red-hand-defenders/example1.jpg'],
  'Royal Black Institution' : ['https://quinfer.github.io/flag-examples/royal-black-institution/example1.jpg']
}

// Flag descriptions for additional context
const flagDescriptions = {
  'European Union': 'The flag of the European Union, featuring a circle of twelve gold stars on a blue background.',
  'Scottish Saltire': 'The flag of Scotland, featuring a white diagonal cross (St. Andrew\'s Cross) on a blue background.',
  'Apprentice Boys': 'Flag associated with the Apprentice Boys of Derry, typically featuring crimson and blue colors with organizational symbols.',
  'Union Jack': 'The national flag of the United Kingdom, featuring red and white crosses on a blue background.',
  'Ulster Banner': 'Former flag of Northern Ireland (1953-1972) with the Red Hand of Ulster on a white star and red cross.',
  'Irish Tricolor': 'The national flag of Ireland with vertical stripes of green, white, and orange.',
  'Orange Order': 'Orange/purple/blue flag with symbols of the Orange Order fraternal organization.',
  'Parachute Regiment': 'Flag of the British Armys Parachute Regiment, featuring a parachute and wings.',
  'Royal Standard': 'The royal banner used by Queen Elizabeth II in her capacity as Sovereign of the United Kingdom.',
  'Northern Ireland Football': 'Flag representing the Northern Ireland national football team.',
  'UVF': 'Ulster Volunteer Force flag, a proscribed loyalist paramilitary organization.',
  'UDA': 'Ulster Defence Association flag, a proscribed loyalist paramilitary organization.',
  'UDR': 'Ulster Defence Regiment flag, a British Army regiment formed in 1970 to replace the B Specials.',
  'UFF': 'Ulster Freedom Fighters flag, a cover name used by the UDA.',
  'YCV': 'Young Citizen Volunteers flag, the youth wing of the UVF.',
  'Other Proscribed': 'Flags of other proscribed paramilitary organizations not specifically listed elsewhere.',
  'WW1 Commemorative': 'Flags commemorating World War I, often featuring poppies or dates 1914-1918.',
  'WW2 Commemorative': 'Flags commemorating World War II, typically featuring dates 1939-1945 and symbols of remembrance.',
  'Royal Irish Regiment': 'Flag of the British Army regiment formed in 1992, featuring a harp and crown on a dark green background.',
  'Israeli': 'The national flag of Israel, featuring a blue Star of David on a white background with blue stripes.',
  'Palestinian': 'The national flag of Palestine, featuring horizontal stripes of black, white, and green with a red triangle on the hoist side.',
  'GAA': 'Flags representing the Gaelic Athletic Association, typically featuring county colors and GAA emblems.',
  'Royal Black Institution': 'Flag of the Protestant fraternal organization, often featuring black, purple and religious symbolism.',
  'Red Hand Defenders': 'Flag of a loyalist paramilitary group, typically featuring the Red Hand of Ulster symbol.',
  'Red/White/Blue Triangular Bunting': 'Decorative triangular cloth pennants in red, white, and blue colors, typically strung along streets or buildings.',
  'Orange/Purple Triangular Bunting': 'Decorative triangular cloth pennants in orange and purple colors, often associated with Orange Order celebrations.',
  'Irish Tricolor Bunting': 'Decorative bunting featuring green, white, and orange triangular pennants resembling the Irish flag.',
  'Union Jack Bunting': 'Decorative bunting featuring Union Jack patterns on triangular pennants.',
  'Mixed Flags Bunting': 'Decorative bunting featuring various flag designs or symbols on triangular pennants.',
  'Other Colored Bunting': 'Generic decorative triangular pennants in colors not falling into the other bunting categories.'
}

export default function ExpertFlagLabeler() {
  const router = useRouter()
  
  // All useState hooks
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [images, setImages] = useState(staticImages || [])
  const [loading, setLoading] = useState(true)
  const [imageError, setImageError] = useState<string | null>(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [primaryCategory, setPrimaryCategory] = useState('')
  const [secondaryCategory, setSecondaryCategory] = useState('')
  const [specificFlag, setSpecificFlag] = useState('')
  const [confidence, setConfidence] = useState(3)
  const [classifications, setClassifications] = useState<Record<string, any>>({})
  const [zoom, setZoom] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [needsReview, setNeedsReview] = useState(false)
  const [reviewReason, setReviewReason] = useState('')
  const [showReviewDialog, setShowReviewDialog] = useState(false)
  const [stats, setStats] = useState({
    labeled: 0,
    flaggedForReview: 0,
    avgConfidence: 0
  })
  const [showAcademicInfo, setShowAcademicInfo] = useState(false)
  const [showExampleModal, setShowExampleModal] = useState(false)
  const [selectedExample, setSelectedExample] = useState<string | null>(null)
  const [showInstructions, setShowInstructions] = useState(false)
  const [currentUser, setCurrentUser] = useState<string | null>(null);
  const [userStats, setUserStats] = useState({
    expert1: 0,
    expert2: 0,
    expert3: 0,
    expert4: 0
  });
  const [currentExampleIndex, setCurrentExampleIndex] = useState(0);
  const [isSaving, setIsSaving] = useState(false);

  // All useEffect hooks
  useEffect(() => {
    const checkAuth = () => {
      const auth = localStorage.getItem('isAuthenticated') === 'true'
      const userData = localStorage.getItem('user')
      
      if (auth && userData) {
        const parsedUser = JSON.parse(userData)
        setIsAuthenticated(true)
        setUser(parsedUser)
      } else {
        router.push('/login')
      }
      setAuthLoading(false)
    }
    checkAuth()
  }, [router])
  
  useEffect(() => {
    async function loadImages() {
      try {
        // Load from the correct API route
        const response = await fetch('/api/images-static');
        const data = await response.json();
        
        if (data.success && data.images && data.images.length > 0) {
          console.log("Successfully loaded images from API:", data.images.length);
          
          // Check if we got any composite images
          const compositesCount = data.images.filter(img => img.has_composite || img.composite_image).length;
          console.log(`API returned ${compositesCount} images with composite data`);
          
          // Sample a few images to debug
          if (data.images.length > 0) {
            console.log("Sample image data:", data.images[0]);
            if (compositesCount > 0) {
              const sampleComposite = data.images.find(img => img.has_composite || img.composite_image);
              console.log("Sample composite image:", sampleComposite);
            }
          }
          
          setImages(data.images || []);
        } else {
          // Fallback to static images
          console.log("Falling back to static images, count:", staticImages.length);
          setImages(staticImages || []);
        }
      } catch (error) {
        console.error("Error loading images:", error);
        // Fallback to static images if API fails
        console.log("API error, falling back to static images, count:", staticImages.length);
        setImages(staticImages || []);
      } finally {
        setLoading(false);
        
        // After images are loaded, restore the user's progress if available
        if (user && user.username) {
          const savedProgress = localStorage.getItem(`progress_${user.username}`)
          if (savedProgress) {
            const savedIndex = parseInt(savedProgress, 10)
            console.log(`Restoring progress for ${user.username}. Saved index: ${savedIndex}`)
            // Make sure the saved index is valid
            if (savedIndex >= 0 && savedIndex < (data?.images?.length || staticImages.length)) {
              setCurrentIndex(savedIndex)
            } else {
              console.log(`Saved index ${savedIndex} is out of range, resetting to 0`)
            }
          }
        }
      }
    }
    
    loadImages();
  }, []);

  useEffect(() => {
    // Function to get the current user from Basic Auth
    const getCurrentUser = async () => {
      try {
        const response = await fetch('/api/current-user')
        const data = await response.json()
        setCurrentUser(data.username)
      } catch (error) {
        console.error('Failed to get current user:', error)
      }
    }
    
    // Only run this if we're authenticated
    if (isAuthenticated) {
      getCurrentUser()
    }
  }, [isAuthenticated])

  // Update this when fetching classifications
  useEffect(() => {
    const fetchUserStats = async () => {
      try {
        const response = await fetch('/api/images-static')
        if (!response.ok) {
          throw new Error('Failed to fetch classifications')
        }
        
        const responseData = await response.json()
        
        // Count classifications by user
        const userCounts = {
          expert1: 0,
          expert2: 0,
          expert3: 0,
          expert4: 0
        }
        
        // Check if responseData.classifications exists before iterating
        if (responseData && responseData.classifications) {
          Object.values(responseData.classifications).forEach((classification: any) => {
            if (classification.expertId && userCounts[classification.expertId] !== undefined) {
              userCounts[classification.expertId]++
            }
          })
        }
        
        setUserStats(userCounts)
      } catch (error) {
        console.error('Error fetching user stats:', error)
      }
    }
    
    // Only fetch user stats if we're authenticated
    if (isAuthenticated) {
      fetchUserStats()
    }
  }, [isAuthenticated])

  // Show instructions on first login
  useEffect(() => {
    const hasSeenInstructions = localStorage.getItem('hasSeenInstructions')
    if (!hasSeenInstructions && isAuthenticated) {
      setShowInstructions(true)
      localStorage.setItem('hasSeenInstructions', 'true')
    }
  }, [isAuthenticated])

  // Initialize images with static images right away
  useEffect(() => {
    if (staticImages && staticImages.length > 0) {
      setImages(staticImages);
      setLoading(false);
    }
  }, []);

  // Get the current image safely
  const currentImage = images && images.length > 0 && currentIndex < images.length 
    ? images[currentIndex] 
    : null;
  
  const handlePrevious = () => {
    if (currentIndex > 0) {
      setImageError(null)  // Reset error state
      setCurrentIndex(currentIndex - 1)
    }
  }

  // Reorganized category structure - updated with specific proscribed flags and bunting
  const flagCategories: FlagCategories = {
    // National flags
    'Union Jack': { primary: 'National', context: 'Political/National Identity' },
    'Ulster Banner': { primary: 'National', context: 'Political/National Identity' },
    'Irish Tricolor': { primary: 'National', context: 'Political/National Identity' },
    'Scottish Saltire': { primary: 'National', context: 'Political/National Identity' },
    'European Union': { primary: 'International', context: 'Political/National Identity' },
    'Royal Standard': { primary: 'National', context: 'Monarchist/Loyalist' },
    
    // Fraternal organizations
    'Orange Order': { primary: 'Fraternal', context: 'Cultural/Religious' },
    'Royal Black Institution': { primary: 'Fraternal', context: 'Cultural/Religious' },
    'Apprentice Boys': { primary: 'Fraternal', context: 'Cultural/Religious' },
    'Red Hand Defenders': { primary: 'Fraternal', context: 'Paramilitary/Political' },
    
    // Sports
    'Northern Ireland Football': { primary: 'Sport', context: 'Sporting' },
    'GAA': { primary: 'Sport', context: 'Sporting' },
    'Local Club': { primary: 'Sport', context: 'Sporting' },
    'Supporters Club': { primary: 'Sport', context: 'Sporting' },
    
    // Military
    'Parachute Regiment': { primary: 'Military', context: 'Military/Memorial' },
    'UDR': { primary: 'Military', context: 'Military/Memorial' },
    'Royal Irish Regiment': { primary: 'Military', context: 'Military/Memorial' },
    'Historical Units': { primary: 'Military', context: 'Military/Memorial' },
    
    // Historical
    'WW1 Commemorative': { primary: 'Historical', context: 'Military/Memorial' },
    'WW2 Commemorative': { primary: 'Historical', context: 'Military/Memorial' },
    'Battle Standards': { primary: 'Historical', context: 'Military/Memorial' },
    'Regimental Colors': { primary: 'Historical', context: 'Military/Memorial' },
    
    // International
    'Palestinian': { primary: 'International', context: 'Political/Solidarity' },
    'Israeli': { primary: 'International', context: 'Political/Solidarity' },
    'Other International': { primary: 'International', context: 'Political/Solidarity' },
    
    // Proscribed - Updated with specific organizations
    'UVF': { primary: 'Proscribed', context: 'Paramilitary/Political' },
    'UDA': { primary: 'Proscribed', context: 'Paramilitary/Political' },
    'UFF': { primary: 'Proscribed', context: 'Paramilitary/Political' },
    'YCV': { primary: 'Proscribed', context: 'Paramilitary/Political' },
    'Other Proscribed': { primary: 'Proscribed', context: 'Paramilitary/Political' },
    
    // Bunting Types (new category)
    'Red/White/Blue Triangular Bunting': { primary: 'Bunting', context: 'Decorative' },
    'Orange/Purple Triangular Bunting': { primary: 'Bunting', context: 'Decorative' },
    'Irish Tricolor Bunting': { primary: 'Bunting', context: 'Decorative' },
    'Union Jack Bunting': { primary: 'Bunting', context: 'Decorative' },
    'Mixed Flags Bunting': { primary: 'Bunting', context: 'Decorative' },
    'Other Colored Bunting': { primary: 'Bunting', context: 'Decorative' }
  }
  
  // Group flags by user-friendly contexts
  const contextGroups = {
    'Political/National Identity': Object.keys(flagCategories).filter(flag => 
      flagCategories[flag].context === 'Political/National Identity'
    ),
    'Cultural/Religious': Object.keys(flagCategories).filter(flag => 
      flagCategories[flag].context === 'Cultural/Religious'
    ),
    'Sporting': Object.keys(flagCategories).filter(flag => 
      flagCategories[flag].context === 'Sporting'
    ),
    'Military/Memorial': Object.keys(flagCategories).filter(flag => 
      flagCategories[flag].context === 'Military/Memorial'
    ),
    'Paramilitary/Political': Object.keys(flagCategories).filter(flag => 
      flagCategories[flag].context === 'Paramilitary/Political'
    ),
    'Political/Solidarity': Object.keys(flagCategories).filter(flag => 
      flagCategories[flag].context === 'Political/Solidarity'
    ),
    'Decorative Bunting': Object.keys(flagCategories).filter(flag => 
      flagCategories[flag].context === 'Decorative'
    )
  }
  
  // Unified display contexts that apply to all flag types
  const displayContexts = [
    'Building-mounted', 
    'Lamppost-mounted',
    'Pole-mounted (in ground)', 
    'Hand-carried', 
    'Vehicle-mounted',
    'Window display',
    'Parade display',
    'Permanent installation',
    'Temporary installation',
    'Memorial/Commemoration',
    'Event-specific',
    'Street decoration',
    'Bunting display', // Added bunting as a display context
    'Triangular bunting'
  ]
  
  // Handle flag selection - automatically sets the primary category
  const handleFlagSelection = (flag: string) => {
    console.log("Selected flag:", flag);
    setSpecificFlag(flag)
    setPrimaryCategory(flagCategories[flag].primary)
    
    // If bunting is selected, automatically set the display context to the appropriate bunting type
    if (flagCategories[flag].primary === 'Bunting') {
      if (flag.includes('Triangular')) {
        setSecondaryCategory('Triangular bunting');
      } else {
        setSecondaryCategory('Bunting display');
      }
    }
  }

  // Function to show example
  const handleShowExample = (flag: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setSelectedExample(flag)
    setCurrentExampleIndex(0)
    setShowExampleModal(true)
  }
  
  const handleSubmitClassification = async (classificationData) => {
    console.log("Button clicked, form data:", classificationData); // Debug logging
    
    if (!currentImage) {
      console.error("No current image to classify");
      alert("Error: No image selected for classification");
      return;
    }
    
    if (!classificationData.primaryCategory && !specificFlag) {
      console.error("No flag category selected");
      alert("Please select a flag type");
      return;
    }
    
    setIsSaving(true);
    
    try {
      // Get the current user from localStorage
      const userData = localStorage.getItem('user');
      const expertId = userData ? JSON.parse(userData).username : 'anonymous';
      
      // Determine if this is a bunting classification
      const isBunting = specificFlag && flagCategories[specificFlag].primary === 'Bunting';
      
      // Construct payload using the form data or component state
      const payload = {
        action: 'save',
        classification: {
          imageId: currentImage.filename,
          town: currentImage.town,
          primaryCategory: specificFlag ? flagCategories[specificFlag].primary : classificationData.primaryCategory,
          specificFlag: specificFlag || classificationData.specificFlag,
          displayContext: classificationData.displayContext || secondaryCategory,
          isBunting: isBunting,
          buntingType: isBunting ? specificFlag : null, // Store bunting type explicitly
          confidence: classificationData.confidence || confidence,
          timestamp: new Date().toISOString(),
          expertId: expertId
        }
      };
      
      console.log("Sending payload:", payload); // Debug logging
      
      // Send the data to the API
      const response = await fetch('/api/classifications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      
      const result = await response.json();
      console.log("API response:", result);
      
      // Update statistics
      setStats(prev => ({
        ...prev,
        labeled: prev.labeled + 1,
        avgConfidence: (prev.avgConfidence * prev.labeled + (classificationData.confidence || confidence)) / (prev.labeled + 1)
      }));
      
      // Move to the next image
      setCurrentIndex(prev => prev + 1);
      
      // Reset form state
      setPrimaryCategory('');
      setSecondaryCategory('');
      setSpecificFlag('');
      setConfidence(3);
      
    } catch (error) {
      console.error("Error submitting classification:", error);
      // Extract response text if available
      let errorMessage = "Failed to save classification";
      if (error.response) {
        try {
          const errorText = await error.response.text();
          errorMessage += ": " + errorText;
        } catch (e) {
          errorMessage += ". See console for details.";
        }
      }
      alert(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  // Add zoom handlers
  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.5, 5)) // Max zoom 5x
  }
  
  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.5, 1)) // Min zoom 1x
  }
  
  const handleResetZoom = () => {
    setZoom(1)
    setPosition({ x: 0, y: 0 })
  }
  
  const handleDragStart = (e: React.MouseEvent) => {
    if (zoom > 1) {
      setIsDragging(true)
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y })
    }
  }
  
  const handleDrag = (e: React.MouseEvent) => {
    if (isDragging && zoom > 1) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      })
    }
  }
  
  const handleDragEnd = () => {
    setIsDragging(false)
  }

  // Handle submitting review
  const handleSubmitReview = async () => {
    if (!reviewReason) {
      alert("Please select a reason for review");
      return;
    }
    
    if (!currentImage) {
      alert("No image selected");
      return;
    }
    
    try {
      console.log("Sending review for image:", currentImage.filename);
      
      // Get the current user from localStorage to ensure we have the latest value
      const userData = localStorage.getItem('user');
      const currentUser = userData ? JSON.parse(userData) : null;
      
      // Create a simpler payload
      const payload = { 
        action: 'flag',
        imageId: currentImage.filename,
        town: currentImage.town || 'Unknown',
        reason: reviewReason,
        expertId: currentUser?.username || currentUser?.name || 'anonymous'
      };
      
      console.log("Sending payload:", payload);
      
      // Use the same endpoint as regular classifications
      const response = await fetch('/api/classifications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("API error response:", errorText);
        throw new Error(`Server responded with ${response.status}: ${errorText}`);
      }
      
      const responseData = await response.json();
      console.log("Review saved successfully:", responseData);
      
      // Update local state
      setClassifications({
        ...classifications,
        [currentImage.filename]: {
          imageId: currentImage.filename,
          needsReview: true,
          reviewReason: reviewReason
        }
      });
      
      // Update statistics
      setStats(prevStats => ({
        ...prevStats,
        flaggedForReview: prevStats.flaggedForReview + 1
      }));
      
      // Reset form and close dialog
      setReviewReason('');
      setShowReviewDialog(false);
      
      // Move to next image
      setImageError(null);
      setCurrentIndex(currentIndex + 1);
    } catch (error) {
      console.error('Error flagging for review:', error);
      alert(`Failed to flag for review: ${error.message || "Unknown error"}`);
    }
  };

  // For flagging images for review
  const flagForReview = async (imageId, reason) => {
    try {
      const response = await fetch('/api/classifications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          action: 'flag',
          imageId,
          town: currentImage?.town || 'Unknown',
          reason: reason || 'Needs review',
          expertId: user?.username || 'anonymous'
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      
      const result = await response.json();
      if (result.success) {
        // Handle success
        console.log('Successfully flagged for review');
        return true;
      } else {
        throw new Error(result.error || 'Unknown error');
      }
    } catch (error) {
      console.error('Error flagging for review:', error);
      alert('Failed to flag for review: ' + error.message);
      return false;
    }
  };

  // For saving classifications
  const saveClassification = async (classification) => {
    try {
      const response = await fetch('/api/classifications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          action: 'save',
          classification: {
            ...classification,
            expertId: user?.username || 'anonymous'
          }
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      
      const result = await response.json();
      if (result.success) {
        // Handle success
        console.log('Successfully saved classification');
        return true;
      } else {
        throw new Error(result.error || 'Unknown error');
      }
    } catch (error) {
      console.error('Error saving classification:', error);
      alert('Failed to save classification: ' + error.message);
      return false;
    }
  };

  // Logout function that saves the current progress
  const handleLogout = () => {
    // Save progress for this user
    if (user && user.username) {
      console.log(`Saving progress for ${user.username}. Current index: ${currentIndex}`)
      localStorage.setItem(`progress_${user.username}`, currentIndex.toString())
    }
    
    // Perform logout
    localStorage.removeItem('isAuthenticated')
    localStorage.removeItem('user')
    router.push('/login')
  }

  // Test API connection when authenticated
  useEffect(() => {
    const testApi = async () => {
      try {
        await fetch('/api/classifications', {
          method: 'GET'
        });
      } catch (error) {
        // Silently fail
      }
    };
    
    if (isAuthenticated) {
      testApi();
    }
  }, [isAuthenticated]);



  // Now your conditional returns
  if (authLoading) {
    return <div className="flex justify-center items-center h-screen">Loading authentication...</div>
  }

  if (!isAuthenticated) {
    return <div className="flex justify-center items-center h-screen">Redirecting to login...</div>
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* Add help button in header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <div>Welcome, {user?.name || "Expert"}</div>
          <div className="text-xs text-gray-500">
            Your progress is automatically saved when you logout
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => {
              // Save progress without logging out
              if (user && user.username) {
                localStorage.setItem(`progress_${user.username}`, currentIndex.toString())
                alert(`Progress saved at image ${currentIndex + 1} of ${images.length}`)
              }
            }}
            className="flex items-center gap-1"
          >
            Save Progress
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setShowInstructions(true)}
            className="flex items-center gap-1"
          >
            <HelpCircle size={16} />
            <span>Help</span>
          </Button>
          <Button variant="outline" size="sm" onClick={handleLogout}>
            Save & Logout
          </Button>
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="flex justify-between items-center p-4">
        <Button 
          variant="outline" 
          onClick={handlePrevious}
          disabled={currentIndex === 0}
        >
          Previous Image
        </Button>
        <div className="flex gap-3">
          <Button 
            variant="outline"
            onClick={() => setShowReviewDialog(true)}
          >
            Flag for Review
          </Button>
          <Button 
            className="bg-green-600 hover:bg-green-700"
            onClick={() => handleSubmitClassification({ 
              primaryCategory: specificFlag ? flagCategories[specificFlag]?.primary : primaryCategory, 
              specificFlag: specificFlag,
              displayContext: secondaryCategory, 
              confidence: confidence 
            })}
            disabled={!specificFlag || isSaving}
          >
            {isSaving ? 'Saving...' : 'Save & Next'}
          </Button>
        </div>
      </div>

      {/* Main Content - Single Column Layout */}
      <div className="grid grid-cols-1 gap-4">
        {/* Image Display Card - Full Width */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Image {currentIndex + 1} of {images.length}</h2>
              <p className="text-sm text-gray-500">Location: {currentImage?.town}</p>
            </div>
            {/* Side-by-side view is always shown by default */}
          </CardHeader>
          <CardContent>
            {/* Image with zoom controls */}
            <div className="relative overflow-hidden border rounded-lg h-[500px] mb-4">
              {!loading && currentImage && (
                <div 
                  className="relative w-full h-full"
                  style={{ 
                    transform: `scale(${zoom}) translate(${position.x}px, ${position.y}px)`,
                    cursor: isDragging ? 'grabbing' : 'grab'
                  }}
                  onMouseDown={handleDragStart}
                  onMouseMove={handleDrag}
                  onMouseUp={handleDragEnd}
                >
                  {currentImage ? (
                    <div>
                      <SimpleCompositeImage
                        croppedSrc={currentImage.path}
                        compositeSrc={currentImage.composite_image}
                        alt={`Flag in ${currentImage.town}`}
                        town={currentImage.town}
                      />
                    </div>
                  ) : (
                    <div className="text-center p-4">
                      <p className="text-red-500 font-medium">Image not available</p>
                      <p className="text-sm text-gray-500 mt-2">
                        Please ensure you have run:<br/>
                        1. python scripts/prepare_images_for_classification.py --side-by-side --copy-to-public<br/>
                        2. node scripts/generate-image-list.js
                      </p>
                    </div>
                  )}
                </div>
              )}
              {imageError && <p className="text-red-500 p-4">{imageError}</p>}
            </div>
            
            {/* Zoom controls in a single row */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setZoom(Math.max(1, zoom - 0.2))}
                >
                  -
                </Button>
                <span className="text-sm">Zoom: {zoom.toFixed(1)}x</span>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setZoom(Math.min(3, zoom + 0.2))}
                >
                  +
                </Button>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => {
                  setZoom(1)
                  setPosition({ x: 0, y: 0 })
                }}
              >
                Reset View
              </Button>
            </div>
          </CardContent>
        </Card>
        
        {/* Classification Card - Full Width */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Classification</h2>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setShowAcademicInfo(!showAcademicInfo)}
              >
                {showAcademicInfo ? "Hide Academic Info" : "Show Academic Info"}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Academic categories explanation */}
            {showAcademicInfo && (
              <div className="bg-blue-50 p-3 rounded-md text-sm">
                <p className="font-medium mb-1">Academic Categorization:</p>
                <p>This tool uses academic categories to organize flags: National, Fraternal, Sport, Military, Historical, International, and Proscribed. Your selections will automatically be mapped to these categories for research purposes.</p>
              </div>
            )}
            
            {/* Flag Type Selection - Using buttons grouped by context */}
            <div>
              <Label className="block mb-2">Flag Type</Label>
              <div className="space-y-4">
                {Object.entries(contextGroups).map(([context, flags]) => (
                  <div key={context} className="border rounded-md p-3">
                    <h4 className="font-medium mb-2">{context}</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {flags.map(flag => (
                        <div key={flag} className="flex items-center">
                          <Button
                            variant={specificFlag === flag ? "default" : "outline"}
                            onClick={() => handleFlagSelection(flag)}
                            className="w-full text-sm justify-between"
                            size="sm"
                          >
                            <span>{flag}</span>
                            {showAcademicInfo && (
                              <span className="ml-1 text-xs opacity-70">
                                ({flagCategories[flag].primary})
                              </span>
                            )}
                          </Button>
                          
                          {/* Example button for flags with examples */}
                          {flagExamples[flag] && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="px-2 ml-1"
                              onClick={(e) => handleShowExample(flag, e)}
                            >
                              <Info className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Display Context - Using dropdown */}
            <div>
              <Label>Display Context</Label>
              <select
                className="w-full p-2 border rounded"
                value={secondaryCategory}
                onChange={(e) => setSecondaryCategory(e.target.value)}
              >
                <option value="">Select display context...</option>
                {displayContexts.map(context => (
                  <option key={context} value={context}>{context}</option>
                ))}
              </select>
            </div>
            
            {/* Bunting guidance - only shown when bunting is selected */}
            {primaryCategory === 'Bunting' && (
              <div className="mt-4 p-3 bg-blue-50 rounded-md">
                <h4 className="text-sm font-medium mb-2">Bunting Classification Guidance</h4>
                <ul className="text-xs space-y-1">
                  <li>• Triangular bunting consists of small triangular pennants strung together</li>
                  <li>• Pay attention to colors and patterns to determine the bunting type</li>
                  <li>• If bunting features distinct flag patterns, select the appropriate bunting type</li>
                  <li>• If you're unsure, use "Flag for Review" and select "Bunting needs specialized review"</li>
                </ul>
              </div>
            )}

            {/* Confidence Slider */}
            <div>
              <Label>Confidence Level (1-5)</Label>
              <Slider
                value={[confidence]}
                onValueChange={(value) => setConfidence(value[0])}
                min={1}
                max={5}
                step={1}
                className="w-full"
              />
              <div className="text-center mt-2">
                Current confidence: {confidence}
              </div>
            </div>
            
            {/* Navigation Controls */}
            <div className="flex justify-between items-center pt-4">
              <Button 
                variant="outline" 
                onClick={handlePrevious}
                disabled={currentIndex === 0}
              >
                Previous Image
              </Button>
              <div className="flex gap-3">
                <Button 
                  variant="outline"
                  onClick={() => setShowReviewDialog(true)}
                >
                  Flag for Review
                </Button>
                <Button 
                  className="bg-green-600 hover:bg-green-700"
                  onClick={() => handleSubmitClassification({ 
                    primaryCategory: specificFlag ? flagCategories[specificFlag]?.primary : primaryCategory, 
                    specificFlag: specificFlag,
                    displayContext: secondaryCategory, 
                    confidence: confidence 
                  })}
                  disabled={!specificFlag || isSaving}
                >
                  {isSaving ? 'Saving...' : 'Save & Next'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Statistics Card */}
      <div className="p-4">
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Session Statistics</h2>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <h3 className="text-sm font-medium text-gray-500">Images Labeled</h3>
                <p className="text-2xl font-bold">{stats.labeled}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <h3 className="text-sm font-medium text-gray-500">Remaining</h3>
                <p className="text-2xl font-bold">{images.length - (currentIndex + 1)}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <h3 className="text-sm font-medium text-gray-500">Avg. Confidence</h3>
                <p className="text-2xl font-bold">{stats.avgConfidence.toFixed(1)}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <h3 className="text-sm font-medium text-gray-500">Flagged for Review</h3>
                <p className="text-2xl font-bold">{stats.flaggedForReview}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Review Dialog */}
      {showReviewDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full">
            <h3 className="text-xl font-bold mb-4">Flag for Review</h3>
            <p className="mb-4">Please select a reason for flagging this image for review:</p>
            
            <div className="space-y-2 mb-6">
              <div className="flex items-center">
                <input 
                  type="radio" 
                  id="not-flag" 
                  name="review-reason" 
                  value="Not a flag"
                  checked={reviewReason === "Not a flag"}
                  onChange={() => setReviewReason("Not a flag")}
                  className="mr-2"
                />
                <label htmlFor="not-flag">Not a flag (e.g., decoration, poster, object)</label>
              </div>
              
              <div className="flex items-center">
                <input 
                  type="radio" 
                  id="unclear" 
                  name="review-reason" 
                  value="Unclear image"
                  checked={reviewReason === "Unclear image"}
                  onChange={() => setReviewReason("Unclear image")}
                  className="mr-2"
                />
                <label htmlFor="unclear">Unclear image</label>
              </div>
              
              <div className="flex items-center">
                <input 
                  type="radio" 
                  id="complex" 
                  name="review-reason" 
                  value="Complex case"
                  checked={reviewReason === "Complex case"}
                  onChange={() => setReviewReason("Complex case")}
                  className="mr-2"
                />
                <label htmlFor="complex">Complex case (needs expert review)</label>
              </div>
              
              {/* Bunting option removed as it's now being classified directly */}
              
              <div className="flex items-center">
                <input 
                  type="radio" 
                  id="other" 
                  name="review-reason" 
                  value="Other"
                  checked={reviewReason === "Other"}
                  onChange={() => setReviewReason("Other")}
                  className="mr-2"
                />
                <label htmlFor="other">Other reason</label>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3">
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowReviewDialog(false)
                  setReviewReason('')
                }}
              >
                Cancel
              </Button>
              <Button 
                onClick={handleSubmitReview}
                disabled={!reviewReason}
              >
                Submit
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Flag Example Modal */}
      {showExampleModal && selectedExample && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full relative">
            {/* Close button */}
            <button 
              onClick={() => setShowExampleModal(false)}
              className="absolute top-2 right-2 w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100"
              aria-label="Close"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
            
            <h3 className="text-xl font-bold mb-4">{selectedExample}</h3>
            
            {flagDescriptions[selectedExample] && (
              <p className="mb-4 text-gray-600">{flagDescriptions[selectedExample]}</p>
            )}
            
            <div className="mb-4 relative">
              {Array.isArray(flagExamples[selectedExample]) && flagExamples[selectedExample].length > 0 ? (
                <>
                  <img 
                    src={flagExamples[selectedExample][currentExampleIndex]} 
                    alt={`Example of ${selectedExample}`} 
                    className="max-w-full h-auto mx-auto"
                    style={{ maxHeight: '250px' }}
                  />
                  
                  {/* Example counter */}
                  <div className="text-center mt-2 text-sm text-gray-500">
                    Example {currentExampleIndex + 1} of {flagExamples[selectedExample].length}
                  </div>
                  
                  {/* Navigation indicators */}
                  <div className="flex justify-center mt-2 space-x-1">
                    {flagExamples[selectedExample].map((_, index) => (
                      <button 
                        key={index}
                        onClick={() => setCurrentExampleIndex(index)}
                        className={`w-2 h-2 rounded-full ${currentExampleIndex === index ? 'bg-blue-600' : 'bg-gray-300'}`}
                        aria-label={`Go to example ${index + 1}`}
                      />
                    ))}
                  </div>
                  
                  {/* Navigation buttons - only show if there are multiple examples */}
                  {flagExamples[selectedExample].length > 1 && (
                    <>
                      <button 
                        onClick={() => setCurrentExampleIndex(prev => (prev === 0 ? flagExamples[selectedExample].length - 1 : prev - 1))}
                        className="absolute left-0 top-1/2 transform -translate-y-1/2 bg-white rounded-full p-1 shadow"
                        aria-label="Previous example"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="15 18 9 12 15 6"></polyline>
                        </svg>
                      </button>
                      <button 
                        onClick={() => setCurrentExampleIndex(prev => (prev === flagExamples[selectedExample].length - 1 ? 0 : prev + 1))}
                        className="absolute right-0 top-1/2 transform -translate-y-1/2 bg-white rounded-full p-1 shadow"
                        aria-label="Next example"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                      </button>
                    </>
                  )}
                </>
              ) : (
                <div className="text-center p-4 bg-gray-100 rounded">
                  No example images available
                </div>
              )}
            </div>
            
            <div className="flex justify-end">
              <Button onClick={() => setShowExampleModal(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Add instructions modal */}
      <InstructionsModal 
        isOpen={showInstructions} 
        onClose={() => setShowInstructions(false)} 
      />

      <div className="text-sm text-gray-500 mb-4">
        Logged in as: <span className="font-medium">{user?.name || 'Unknown'}</span>
      </div>
    </div>
  )
}