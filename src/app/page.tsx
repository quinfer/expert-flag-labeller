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
  'Union Jack': '/FlagExamples/UnionJack/SVrJ9GHs2MNRS4AbrknDpg_300.jpg',
  'Ulster Banner': '/FlagExamples/Ulsterbanner/rD5NsqK3M-RI9qor-WzriA_300.jpg',
  'Irish Tricolor': '/FlagExamples/Tricolour/UHmCuSmTD7Omx6X3mqah3A_180.jpg',
  'Orange Order': '/FlagExamples/Orange Order/nyB_fNQFb8p5dHTry91OFA_300.jpg',
  'Parachute Regiment': '/FlagExamples/Parachute/JXbrwyqANo11c-ecWdFkbg_000.jpg',
  'Royal Standard': '/FlagExamples/Royal Standard/5vQ7BsIGqN5gUtgJPCdpjw_000.jpg',
  'Northern Ireland Football': '/FlagExamples/NIF/4LfB1oH4L4OXBCybpD1pQg_240.jpg',
  'UVF': '/FlagExamples/UVF/kXdKzHVCLjA9FJMAJWaTYQ_300.jpg',
  'UDA': '/FlagExamples/UDA/dH80pDtsYDfXRSq0upE3nQ_300.jpg',
  'UFF': '/FlagExamples/UFF/KuyWw9KQ8hZEvZioxDHVlw_300.jpg',
  'YCV': '/FlagExamples/YCV/D-PFjWZmllg4ovARHOWPkA_180.jpg',
  'WW1 Commemorative': '/FlagExamples/WWI/ZP0N_nSRu_DKVHzSH17y9A_120.jpg',
  'Israeli': '/FlagExamples/Israel/HLIf8zO9MACoRn0kKc8y9A_300.jpg'
}

// Flag descriptions for additional context
const flagDescriptions = {
  'Union Jack': 'The national flag of the United Kingdom, featuring red and white crosses on a blue background.',
  'Ulster Banner': 'Former flag of Northern Ireland (1953-1972) with the Red Hand of Ulster on a white star and red cross.',
  'Irish Tricolor': 'The national flag of Ireland with vertical stripes of green, white, and orange.',
  'Orange Order': 'Orange/purple/blue flag with symbols of the Orange Order fraternal organization.',
  'Parachute Regiment': 'Flag of the British Armys Parachute Regiment, featuring a parachute and wings.',
  'Royal Standard': 'The royal banner used by Queen Elizabeth II in her capacity as Sovereign of the United Kingdom.',
  'Northern Ireland Football': 'Flag representing the Northern Ireland national football team.',
  'UVF': 'Ulster Volunteer Force flag, a proscribed loyalist paramilitary organization.',
  'UDA': 'Ulster Defence Association flag, a proscribed loyalist paramilitary organization.',
  'UFF': 'Ulster Freedom Fighters flag, a cover name used by the UDA.',
  'YCV': 'Young Citizen Volunteers flag, the youth wing of the UVF.',
  'WW1 Commemorative': 'Flags commemorating World War I, often featuring poppies or dates 1914-1918.',
  'Israeli': 'The national flag of Israel, featuring a blue Star of David on a white background with blue stripes.'
}

export default function ExpertFlagLabeler() {
  const router = useRouter()
  
  // All useState hooks
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [images, setImages] = useState<ImageData[]>([])
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

  // All useEffect hooks
  useEffect(() => {
    const checkAuth = () => {
      const auth = localStorage.getItem('isAuthenticated') === 'true'
      const userData = localStorage.getItem('user')
      
      if (auth && userData) {
        setIsAuthenticated(true)
        setUser(JSON.parse(userData))
      } else {
        router.push('/login')
      }
      setAuthLoading(false)
    }
    checkAuth()
  }, [router])
  
  useEffect(() => {
    const fetchImages = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/images-static')
        const data = await response.json()
        setImages(data.images)
      } catch (error) {
        console.error('Failed to fetch images:', error)
      } finally {
        setLoading(false)
      }
    }
    if (isAuthenticated) {
      fetchImages()
    }
  }, [isAuthenticated])

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

  const currentImage = images[currentIndex]
  
  const handlePrevious = () => {
    if (currentIndex > 0) {
      setImageError(null)  // Reset error state
      setCurrentIndex(currentIndex - 1)
    }
  }

  // Reorganized category structure - updated with specific proscribed flags
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
    'Purple Star': { primary: 'Fraternal', context: 'Cultural/Religious' },
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
    'Other Proscribed': { primary: 'Proscribed', context: 'Paramilitary/Political' }
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
    'Street decoration'
  ]
  
  // Handle flag selection - automatically sets the primary category
  const handleFlagSelection = (flag: string) => {
    console.log("Selected flag:", flag);
    setSpecificFlag(flag)
    setPrimaryCategory(flagCategories[flag].primary)
  }

  // Function to show example
  const handleShowExample = (flag: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setSelectedExample(flag)
    setShowExampleModal(true)
  }
  
  const handleNext = async () => {
    console.log("Current specificFlag:", specificFlag);
    console.log("Button should be disabled:", !specificFlag);
    
    if (!specificFlag) {
      alert("Please select a specific flag type");
      return;
    }
    
    // Get the current user from localStorage
    const userData = localStorage.getItem('user');
    const user = userData ? JSON.parse(userData) : null;
    
    // Create the classification object with the user's username
    const classification = {
      imageId: images[currentIndex].filename,
      town: images[currentIndex].town,
      primaryCategory,
      specificFlag,
      displayContext: secondaryCategory,
      userContext: flagCategories[specificFlag].context,
      confidence,
      timestamp: new Date().toISOString(),
      expertId: user?.username || user?.name || 'anonymous',
      needsReview: false,
      reviewReason: ''
    }

    try {
      console.log("Sending classification:", classification);
      
      // Save classification to API
      const response = await fetch('/api/classifications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'save',
          classification,
        }),
      })
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Failed to save classification');
      }
      
      // Update local state
      setClassifications({
        ...classifications,
        [images[currentIndex].filename]: classification
      })
      
      // Update statistics
      setStats(prevStats => ({
        ...prevStats,
        labeled: prevStats.labeled + 1,
        avgConfidence: (prevStats.avgConfidence * prevStats.labeled + confidence) / (prevStats.labeled + 1)
      }))
      
      // Reset for the next image
      setImageError(null)
      setCurrentIndex(currentIndex + 1)
      setPrimaryCategory('')
      setSecondaryCategory('')
      setSpecificFlag('')
      setConfidence(3)
    } catch (error) {
      console.error('Failed to save classification:', error);
      setImageError(`Failed to save classification: ${error.message}`);
    }
  }

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

  // Replace signOut with simple logout
  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated')
    localStorage.removeItem('user')
    router.push('/login')
  }

  // Move this useEffect up here, before any conditional returns
  useEffect(() => {
    const testApi = async () => {
      try {
        const response = await fetch('/api/classifications', {
          method: 'GET'
        });
        const data = await response.json();
        console.log("API connection test successful:", data);
      } catch (error) {
        console.error("API connection test failed:", error);
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
        <div>Welcome, {user?.name || "Expert"}</div>
        <div className="flex items-center gap-2">
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
            Logout
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
            onClick={handleNext}
            disabled={!specificFlag}
          >
            Save & Next
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Image Display Card */}
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Image {currentIndex + 1} of {images.length}</h2>
            <p className="text-sm text-gray-500">Location: {currentImage?.town}</p>
          </CardHeader>
          <CardContent>
            {/* Image with zoom controls */}
            <div className="relative overflow-hidden border rounded-lg h-[400px] mb-4">
              {currentImage && (
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
                  <Image
                    src={currentImage.path}
                    alt={`Flag in ${currentImage.town}`}
                    fill
                    style={{ objectFit: 'contain' }}
                    onError={() => setImageError("Failed to load image")}
                  />
                </div>
              )}
              {imageError && <p className="text-red-500 p-4">{imageError}</p>}
            </div>
            
            {/* Zoom controls */}
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
        
        {/* Classification Card */}
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
                  onClick={handleNext}
                  disabled={!specificFlag}
                >
                  Save & Next
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
                <label htmlFor="not-flag">Not a flag (e.g., bunting, decoration)</label>
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
              
              <div className="flex items-center">
                <input 
                  type="radio" 
                  id="bunting" 
                  name="review-reason" 
                  value="Bunting"
                  checked={reviewReason === "Bunting"}
                  onChange={() => setReviewReason("Bunting")}
                  className="mr-2"
                />
                <label htmlFor="bunting">Bunting (not a traditional flag)</label>
              </div>
              
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
            {/* Add close button in the top-right corner */}
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
            
            <div className="mb-4">
              <img 
                src={flagExamples[selectedExample]} 
                alt={`Example of ${selectedExample}`} 
                className="max-w-full h-auto mx-auto"
                style={{ maxHeight: '300px' }}
              />
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