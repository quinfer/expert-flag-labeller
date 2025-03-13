import React from 'react';
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface InstructionsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function InstructionsModal({ isOpen, onClose }: InstructionsModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold">Flag Classification Instructions</h2>
                <p className="text-sm text-gray-500">How to use the Expert Flag Labeler tool</p>
              </div>
              <Button variant="ghost" size="sm" onClick={onClose}>✕</Button>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            <section>
              <h3 className="font-semibold text-lg">Classification Process</h3>
              <p className="mt-2">
                Your task is to classify the bounded flag in each Google Street View image by following these steps:
              </p>
              
              <ol className="list-decimal pl-5 mt-2 space-y-2">
                <li>
                  <strong>Select a Primary Category</strong> - Choose the most appropriate category for the flag shown in the image.
                </li>
                <li>
                  <strong>Select Display Context</strong> - From the dropdown menu, select where and how the flag is being displayed.
                </li>
                <li>
                  <strong>Select Specific Flag</strong> - If applicable, choose the specific flag type from the dropdown options.
                </li>
                <li>
                  <strong>Rate Your Confidence</strong> - Use the slider to indicate how confident you are in your classification (1-5).
                </li>
                <li>
                  <strong>Save & Continue</strong> - Click the "Save & Next" button to submit your classification and move to the next image.
                </li>
              </ol>
            </section>
            
            <section>
              <h3 className="font-semibold text-lg">Flagging Images for Review</h3>
              <p className="mt-2">
                If you encounter an image with issues, click the "Flag for Review" button. You can select from these reasons:
              </p>
              
              <ul className="list-disc pl-5 mt-2">
                <li><strong>Not a flag</strong> - The image shows a decoration or other non-flag item (note: bunting should be classified, not flagged)</li>
                <li><strong>Unclear image</strong> - The image is too blurry, dark, or otherwise difficult to classify</li>
                <li><strong>Complex case</strong> - The image requires additional expert review</li>
                <li><strong>Other reason</strong> - Any other issue not covered by the options above</li>
              </ul>
            </section>
            
            <section>
              <h3 className="font-semibold text-lg">Navigation</h3>
              <p className="mt-2">
                Use the "Previous Image" and "Save & Next" buttons to navigate between images.
              </p>
            </section>
            
            <section>
              <h3 className="font-semibold text-lg">Saving Your Progress</h3>
              <p className="mt-2">
                Your progress is automatically saved when you logout, allowing you to return exactly where you left off when you log back in.
              </p>
              <p className="mt-2">
                You can also use the "Save Progress" button at any time to manually save your current position without logging out. This is useful for marking important points in your classification work.
              </p>
            </section>
            
            <div className="flex justify-end mt-4">
              <Button onClick={onClose}>Close Instructions</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
