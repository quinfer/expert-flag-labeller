'use client';

import { useState } from 'react';

// Define form field options
const PRIMARY_CATEGORIES = [
  { value: '', label: 'Select a category' },
  { value: 'union', label: 'Union Flag' },
  { value: 'ulster', label: 'Ulster Banner' },
  { value: 'irish', label: 'Irish Tricolour' },
  { value: 'paramilitary', label: 'Paramilitary' },
  { value: 'palestine', label: 'Palestinian' },
  { value: 'other', label: 'Other' },
  { value: 'not_flag', label: 'Not a Flag' },
];

const DISPLAY_CONTEXTS = [
  { value: '', label: 'Select context' },
  { value: 'individual', label: 'Individual Flag' },
  { value: 'bunting', label: 'Bunting' },
  { value: 'mural', label: 'Mural' },
  { value: 'shop', label: 'Shop Display' },
  { value: 'protest', label: 'Protest' },
  { value: 'other', label: 'Other' },
];

const CONFIDENCE_LEVELS = [
  { value: 'high', label: 'High Confidence' },
  { value: 'medium', label: 'Medium Confidence' },
  { value: 'low', label: 'Low Confidence' },
  { value: 'unsure', label: 'Unsure/Cannot Determine' },
];

export default function FlagClassificationForm({ onSubmit, isSubmitting, imageData }) {
  // Initialize form state
  const [formData, setFormData] = useState({
    primaryCategory: '',
    displayContext: '',
    specificFlag: '',
    confidence: 'high',
    notes: '',
  });

  // Handle form input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Submit button clicked');
    console.log('Form data:', formData);
    
    // Check if formData is valid
    if (!formData.primaryCategory) {
      console.error('Primary category is missing');
      alert('Please select a primary category');
      return;
    }
    
    // Log before calling onSubmit
    console.log('About to call parent onSubmit function');
    onSubmit(formData);
    console.log('Parent onSubmit function called');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Primary Category Field */}
      <div>
        <label htmlFor="primaryCategory" className="block text-sm font-medium text-gray-700 mb-1">
          Primary Category <span className="text-red-500">*</span>
        </label>
        <select
          id="primaryCategory"
          name="primaryCategory"
          value={formData.primaryCategory}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          {PRIMARY_CATEGORIES.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Display Context Field */}
      <div>
        <label htmlFor="displayContext" className="block text-sm font-medium text-gray-700 mb-1">
          Display Context <span className="text-red-500">*</span>
        </label>
        <select
          id="displayContext"
          name="displayContext"
          value={formData.displayContext}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          {DISPLAY_CONTEXTS.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Specific Flag Field (conditionally shown) */}
      {formData.primaryCategory === 'other' && (
        <div>
          <label htmlFor="specificFlag" className="block text-sm font-medium text-gray-700 mb-1">
            Specific Flag Type <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="specificFlag"
            name="specificFlag"
            value={formData.specificFlag}
            onChange={handleChange}
            required
            placeholder="Please specify the flag type"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      )}

      {/* Confidence Level Field */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Classification Confidence
        </label>
        <div className="space-y-2">
          {CONFIDENCE_LEVELS.map(level => (
            <div key={level.value} className="flex items-center">
              <input
                type="radio"
                id={`confidence-${level.value}`}
                name="confidence"
                value={level.value}
                checked={formData.confidence === level.value}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
              />
              <label htmlFor={`confidence-${level.value}`} className="ml-2 text-sm text-gray-700">
                {level.label}
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Notes Field */}
      <div>
        <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
          Additional Notes
        </label>
        <textarea
          id="notes"
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          rows={3}
          placeholder="Any additional observations"
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Image metadata display */}
      {imageData?.distance_hint && (
        <div className="bg-blue-50 p-3 rounded-md text-sm">
          <div className="font-semibold">Detection Info:</div>
          <div>{imageData.distance_hint}</div>
          {imageData.confidence && (
            <div>Detector confidence: {(imageData.confidence * 100).toFixed(0)}%</div>
          )}
        </div>
      )}

      {/* Submit Button */}
      <div className="pt-4">
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Saving...' : 'Save and Next'}
        </button>
      </div>
    </form>
  );
}
