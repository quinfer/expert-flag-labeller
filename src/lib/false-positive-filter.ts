// src/lib/false-positive-filter.ts
import falsePositivesData from '../data/false-positives-lookup-all.json'

interface FalsePositiveData {
  false_positives: string[]
  count: number
  metadata?: {
    total_towns?: number
    overall_fp_rate?: number
  }
}

interface FilterStats {
  initialized: boolean
  falsePositiveCount: number
  totalTowns: number
  overallFpRate: number
  dataSource: string
}

class FalsePositiveFilter {
  private falsePositives: Set<string>
  private initialized = false
  private metadata: any = {}

  constructor() {
    this.falsePositives = new Set()
    this.initialize()
  }

  private initialize() {
    try {
      const data = falsePositivesData as FalsePositiveData
      this.falsePositives = new Set(data.false_positives)
      this.metadata = data.metadata || {}
      this.initialized = true
      
      const totalTowns = this.metadata.total_towns || 1
      const fpRate = this.metadata.overall_fp_rate || 0
      
      console.log(`✅ False positive filter initialized:`)
      console.log(`   📊 ${data.count} false positives from ${totalTowns} towns`)
      console.log(`   📈 Overall false positive rate: ${fpRate.toFixed(1)}%`)
    } catch (error) {
      console.error('❌ Failed to initialize false positive filter:', error)
      this.initialized = false
    }
  }

  /**
   * Check if an image is a false positive
   */
  isFalsePositive(filename: string): boolean {
    if (!this.initialized) {
      console.warn('⚠️  False positive filter not initialized')
      return false
    }

    // Handle different filename formats
    const normalizedFilename = this.normalizeFilename(filename)
    return this.falsePositives.has(normalizedFilename)
  }

  /**
   * Filter out false positives from an array of images
   */
  filterTruePositives<T extends { path?: string, filename?: string }>(images: T[]): {
    filtered: T[]
    stats: {
      original: number
      filtered: number
      removed: number
      removedPercentage: number
    }
  } {
    if (!this.initialized) {
      console.warn('⚠️  False positive filter not initialized, returning all images')
      return {
        filtered: images,
        stats: {
          original: images.length,
          filtered: images.length,
          removed: 0,
          removedPercentage: 0
        }
      }
    }

    const filtered = images.filter(image => {
      const filename = this.extractFilename(image)
      if (!filename) return true // Keep if we can't determine filename
      
      return !this.isFalsePositive(filename)
    })

    const removedCount = images.length - filtered.length
    const removedPercentage = images.length > 0 ? (removedCount / images.length) * 100 : 0

    if (removedCount > 0) {
      console.log(`🔍 Filtered out ${removedCount} false positive images (${removedPercentage.toFixed(1)}%)`)
    }

    return {
      filtered,
      stats: {
        original: images.length,
        filtered: filtered.length,
        removed: removedCount,
        removedPercentage
      }
    }
  }

  /**
   * Get statistics about false positive filtering
   */
  getStats(): FilterStats {
    return {
      initialized: this.initialized,
      falsePositiveCount: this.falsePositives.size,
      totalTowns: this.metadata.total_towns || 1,
      overallFpRate: this.metadata.overall_fp_rate || 0,
      dataSource: this.metadata.total_towns > 1 ? 'comprehensive' : 'single-town'
    }
  }

  /**
   * Get detailed filtering statistics for API responses
   */
  getDetailedStats(originalCount: number, filteredCount: number) {
    const removed = originalCount - filteredCount
    const removedPercentage = originalCount > 0 ? (removed / originalCount) * 100 : 0

    return {
      filtering: {
        enabled: this.initialized,
        original_count: originalCount,
        filtered_count: filteredCount,
        removed_count: removed,
        removed_percentage: removedPercentage,
        total_false_positives: this.falsePositives.size,
        total_towns: this.metadata.total_towns || 1,
        overall_fp_rate: this.metadata.overall_fp_rate || 0
      }
    }
  }

  private normalizeFilename(filename: string): string {
    // Remove path if present
    const basename = filename.split('/').pop() || filename
    
    // Ensure .jpg extension
    if (!basename.endsWith('.jpg')) {
      return basename + '.jpg'
    }
    
    return basename
  }

  private extractFilename(image: any): string | null {
    // Try different ways to extract filename
    if (image.path) {
      return this.normalizeFilename(image.path)
    }
    if (image.filename) {
      return this.normalizeFilename(image.filename)
    }
    if (typeof image === 'string') {
      return this.normalizeFilename(image)
    }
    
    return null
  }
}

// Export singleton instance
export const falsePositiveFilter = new FalsePositiveFilter()

// Export for testing
export { FalsePositiveFilter } 