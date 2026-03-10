#!/usr/bin/env python3
"""
Intelligent Video Router - Smart Selection Between MoviePy (Free) and Creatomate (Paid)

Automatically chooses the best video generation method based on:
- Complexity of requirements
- Recent success rates
- Cost optimization
- Performance history

Built-in logging and analytics track every decision for cost optimization.

Usage:
    python intelligent_video_router.py --images URL1,URL2 --headline "Transform" --cta "Start Now"
    python intelligent_video_router.py --stats  # View usage statistics
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Import video generators
from moviepy_video_generator import MoviePyVideoGenerator
from creatomate_api import CreatomateAPI

load_dotenv()


class IntelligentVideoRouter:
    """
    Intelligent router that selects between MoviePy (free) and Creatomate (paid).
    
    Decision Logic:
    1. Try MoviePy first for simple videos (70-80% success rate expected)
    2. Fall back to Creatomate if MoviePy fails
    3. Use Creatomate directly for complex requirements
    4. Track all decisions for analytics
    
    Cost Optimization:
    - MoviePy: $0 per video
    - Creatomate: $0.05 per video
    - Target: 70% MoviePy usage = $0.015 average cost per video
    """
    
    def __init__(self, log_dir: str = ".tmp/logs"):
        """
        Initialize intelligent video router.
        
        Args:
            log_dir: Directory for log files
        """
        self.moviepy = MoviePyVideoGenerator()
        self.creatomate = CreatomateAPI()
        
        # Setup logging
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "video_generation.jsonl"
    
    def create_video(
        self,
        image_urls: List[str],
        headline: str,
        cta_text: str,
        duration: float = 15.0,
        music_style: str = "energetic",
        force_method: Optional[str] = None,
        complexity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create video using intelligent routing.
        
        Args:
            image_urls: List of image URLs
            headline: Headline text
            cta_text: CTA text
            duration: Video duration in seconds
            music_style: Background music style
            force_method: Override auto-selection ('moviepy' or 'creatomate')
            complexity: Override complexity detection ('simple' or 'complex')
            
        Returns:
            Dict with success status, video path/URL, method used, and cost
        """
        print(f"\n{'='*70}")
        print("INTELLIGENT VIDEO ROUTER")
        print(f"{'='*70}")
        
        # Log request
        request_data = {
            'timestamp': datetime.now().isoformat(),
            'images': len(image_urls),
            'headline': headline[:50] + '...' if len(headline) > 50 else headline,
            'duration': duration
        }
        
        # Determine complexity
        if complexity is None:
            complexity = self._analyze_complexity(headline, cta_text, image_urls)
        
        print(f"Complexity: {complexity}")
        request_data['complexity'] = complexity
        
        # Get recent performance
        moviepy_success_rate = self._get_success_rate('moviepy', days=7)
        print(f"MoviePy recent success rate: {moviepy_success_rate*100:.1f}%")
        
        # Decision logic
        method_to_try = force_method if force_method else self._decide_method(
            complexity, moviepy_success_rate
        )
        
        print(f"Decision: Try {method_to_try} first")
        
        result = None
        
        # Try MoviePy first (unless forced to Creatomate)
        if method_to_try == 'moviepy':
            print(f"\n{'='*70}")
            print("ATTEMPTING: MoviePy (Local, Free)")
            print(f"{'='*70}")
            
            try:
                result = self.moviepy.create_fitness_ad(
                    image_urls=image_urls,
                    headline=headline,
                    cta_text=cta_text,
                    duration=duration,
                    music_style=music_style
                )
                
                # Validate result
                if result.get('success') and self._validate_video_result(result):
                    self._log_result('moviepy', True, 0, request_data)
                    print(f"\n✓ SUCCESS: MoviePy generated video (Cost: $0)")
                    return result
                else:
                    error = result.get('error', 'Validation failed')
                    print(f"\n✗ MoviePy failed: {error}")
                    self._log_result('moviepy', False, 0, request_data, error=error)
            
            except Exception as e:
                print(f"\n✗ MoviePy exception: {e}")
                self._log_result('moviepy', False, 0, request_data, error=str(e))
        
        # Fall back to Creatomate
        print(f"\n{'='*70}")
        print("FALLBACK: Creatomate (Cloud, $0.05)")
        print(f"{'='*70}")
        
        try:
            result = self.creatomate.create_fitness_ad(
                image_urls=image_urls,
                headline=headline,
                cta_text=cta_text,
                duration=duration,
                music_style=music_style
            )
            
            if result.get('success'):
                self._log_result('creatomate', True, 0.05, request_data)
                print(f"\n✓ SUCCESS: Creatomate generated video (Cost: $0.05)")
                return result
            else:
                error = result.get('error', 'Unknown error')
                print(f"\n✗ Creatomate failed: {error}")
                self._log_result('creatomate', False, 0.05, request_data, error=error)
                return result
        
        except Exception as e:
            print(f"\n✗ Creatomate exception: {e}")
            self._log_result('creatomate', False, 0.05, request_data, error=str(e))
            return {
                'success': False,
                'error': f'All methods failed. Last error: {str(e)}',
                'method': 'creatomate'
            }
    
    def _analyze_complexity(
        self,
        headline: str,
        cta_text: str,
        image_urls: List[str]
    ) -> str:
        """
        Analyze video complexity to determine best generation method.
        
        Simple videos:
        - Standard text overlays
        - 4 images or fewer
        - Short headline (< 80 chars)
        - Basic transitions
        
        Complex videos:
        - Long or multi-line headlines
        - More than 4 images
        - Special characters or emojis
        
        Args:
            headline: Headline text
            cta_text: CTA text
            image_urls: List of images
            
        Returns:
            'simple' or 'complex'
        """
        complexity_score = 0
        
        # Check headline length
        if len(headline) > 80:
            complexity_score += 2
        
        # Check for multi-line text
        if '\n' in headline or '\n' in cta_text:
            complexity_score += 2
        
        # Check number of images
        if len(image_urls) > 4:
            complexity_score += 1
        
        # Check for special characters/emojis
        if any(ord(c) > 127 for c in headline + cta_text):
            complexity_score += 1
        
        # Determine complexity
        return 'complex' if complexity_score >= 3 else 'simple'
    
    def _decide_method(self, complexity: str, moviepy_success_rate: float) -> str:
        """
        Decide which method to try first based on complexity and performance.
        
        Args:
            complexity: 'simple' or 'complex'
            moviepy_success_rate: Recent MoviePy success rate (0.0 to 1.0)
            
        Returns:
            'moviepy' or 'creatomate'
        """
        # Always try MoviePy first (it's free!)
        # Creatomate is only used as automatic fallback if MoviePy fails
        # This maximizes cost savings while ensuring reliability
        return 'moviepy'
    
    def _validate_video_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate that the video result is usable.
        
        Args:
            result: Video generation result dict
            
        Returns:
            True if video is valid
        """
        if not result.get('success'):
            return False
        
        # Check for video path or URL
        video_path = result.get('video_path') or result.get('video_url')
        if not video_path:
            return False
        
        # If local file, check it exists and has reasonable size
        if result.get('video_path'):
            path = Path(result['video_path'])
            if not path.exists():
                return False
            if path.stat().st_size < 10000:  # < 10KB is suspicious
                return False
        
        return True
    
    def _log_result(
        self,
        method: str,
        success: bool,
        cost: float,
        request_data: Dict[str, Any],
        error: Optional[str] = None
    ):
        """
        Log video generation result to JSONL file.
        
        Args:
            method: 'moviepy' or 'creatomate'
            success: Whether generation succeeded
            cost: Cost in USD
            request_data: Request metadata
            error: Error message if failed
        """
        log_entry = {
            **request_data,
            'method': method,
            'success': success,
            'cost': cost,
            'error': error
        }
        
        # Append to JSONL file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _get_success_rate(self, method: str, days: int = 7) -> float:
        """
        Calculate success rate for a method over recent days.
        
        Args:
            method: 'moviepy' or 'creatomate'
            days: Number of days to look back
            
        Returns:
            Success rate (0.0 to 1.0)
        """
        if not self.log_file.exists():
            return 0.85  # Default optimistic rate for MoviePy
        
        cutoff_date = datetime.now() - timedelta(days=days)
        total = 0
        successful = 0
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Check if entry is for this method and within time window
                        if entry.get('method') != method:
                            continue
                        
                        entry_date = datetime.fromisoformat(entry['timestamp'])
                        if entry_date < cutoff_date:
                            continue
                        
                        total += 1
                        if entry.get('success'):
                            successful += 1
                    except:
                        continue
            
            if total == 0:
                return 0.85  # Default rate if no data
            
            return successful / total
        
        except Exception as e:
            print(f"Warning: Failed to read logs: {e}")
            return 0.85
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get usage statistics for the specified time period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with detailed statistics
        """
        if not self.log_file.exists():
            return {
                'total_videos': 0,
                'total_cost': 0,
                'message': 'No data yet'
            }
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stats = {
            'moviepy': {'total': 0, 'success': 0, 'failed': 0, 'cost': 0},
            'creatomate': {'total': 0, 'success': 0, 'failed': 0, 'cost': 0}
        }
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Check time window
                        entry_date = datetime.fromisoformat(entry['timestamp'])
                        if entry_date < cutoff_date:
                            continue
                        
                        method = entry.get('method')
                        if method not in stats:
                            continue
                        
                        stats[method]['total'] += 1
                        stats[method]['cost'] += entry.get('cost', 0)
                        
                        if entry.get('success'):
                            stats[method]['success'] += 1
                        else:
                            stats[method]['failed'] += 1
                    except:
                        continue
        except Exception as e:
            return {'error': f'Failed to read logs: {e}'}
        
        # Calculate totals
        total_videos = stats['moviepy']['total'] + stats['creatomate']['total']
        total_successful = stats['moviepy']['success'] + stats['creatomate']['success']
        total_cost = stats['moviepy']['cost'] + stats['creatomate']['cost']
        
        # Calculate percentages
        moviepy_pct = (stats['moviepy']['success'] / total_videos * 100) if total_videos > 0 else 0
        creatomate_pct = (stats['creatomate']['success'] / total_videos * 100) if total_videos > 0 else 0
        
        # Calculate success rates
        moviepy_success_rate = (stats['moviepy']['success'] / stats['moviepy']['total'] * 100) if stats['moviepy']['total'] > 0 else 0
        creatomate_success_rate = (stats['creatomate']['success'] / stats['creatomate']['total'] * 100) if stats['creatomate']['total'] > 0 else 0
        
        # Cost projections
        avg_cost = total_cost / total_successful if total_successful > 0 else 0
        projected_cost_200 = avg_cost * 200
        creatomate_only_cost_200 = 200 * 0.05
        monthly_savings = creatomate_only_cost_200 - projected_cost_200
        yearly_savings = monthly_savings * 12
        
        return {
            'period_days': days,
            'total_videos': total_videos,
            'total_successful': total_successful,
            'total_cost': total_cost,
            'average_cost_per_video': avg_cost,
            'moviepy': {
                'total_attempts': stats['moviepy']['total'],
                'successful': stats['moviepy']['success'],
                'failed': stats['moviepy']['failed'],
                'success_rate': moviepy_success_rate,
                'percentage_of_total': moviepy_pct,
                'total_cost': stats['moviepy']['cost']
            },
            'creatomate': {
                'total_attempts': stats['creatomate']['total'],
                'successful': stats['creatomate']['success'],
                'failed': stats['creatomate']['failed'],
                'success_rate': creatomate_success_rate,
                'percentage_of_total': creatomate_pct,
                'total_cost': stats['creatomate']['cost']
            },
            'cost_analysis': {
                'projected_monthly_cost_200_videos': projected_cost_200,
                'creatomate_only_cost_200_videos': creatomate_only_cost_200,
                'monthly_savings': monthly_savings,
                'yearly_savings': yearly_savings
            }
        }
    
    def print_statistics(self, days: int = 30):
        """
        Print formatted usage statistics.
        
        Args:
            days: Number of days to analyze
        """
        stats = self.get_statistics(days)
        
        if 'error' in stats:
            print(f"Error: {stats['error']}")
            return
        
        if stats['total_videos'] == 0:
            print("No video generation data yet.")
            return
        
        print(f"\n{'='*70}")
        print(f"VIDEO GENERATION STATISTICS (Last {days} Days)")
        print(f"{'='*70}\n")
        
        print(f"Total Videos Generated: {stats['total_successful']}")
        print(f"Total Cost: ${stats['total_cost']:.2f}")
        print(f"Average Cost per Video: ${stats['average_cost_per_video']:.3f}")
        print()
        
        print(f"{'='*70}")
        print("METHOD BREAKDOWN")
        print(f"{'='*70}\n")
        
        # MoviePy stats
        mp = stats['moviepy']
        print(f"MoviePy (Local, Free):")
        print(f"  Total Attempts:  {mp['total_attempts']}")
        print(f"  Successful:      {mp['successful']} ({mp['percentage_of_total']:.1f}% of total)")
        print(f"  Failed:          {mp['failed']}")
        print(f"  Success Rate:    {mp['success_rate']:.1f}%")
        print(f"  Total Cost:      ${mp['total_cost']:.2f}")
        print()
        
        # Creatomate stats
        cm = stats['creatomate']
        print(f"Creatomate (Cloud, $0.05):")
        print(f"  Total Attempts:  {cm['total_attempts']}")
        print(f"  Successful:      {cm['successful']} ({cm['percentage_of_total']:.1f}% of total)")
        print(f"  Failed:          {cm['failed']}")
        print(f"  Success Rate:    {cm['success_rate']:.1f}%")
        print(f"  Total Cost:      ${cm['total_cost']:.2f}")
        print()
        
        # Cost analysis
        print(f"{'='*70}")
        print("COST ANALYSIS & PROJECTIONS")
        print(f"{'='*70}\n")
        
        ca = stats['cost_analysis']
        print(f"Projected cost at 200 videos/month:")
        print(f"  Your hybrid system:  ${ca['projected_monthly_cost_200_videos']:.2f}/month")
        print(f"  Creatomate-only:     ${ca['creatomate_only_cost_200_videos']:.2f}/month")
        print(f"  Monthly savings:     ${ca['monthly_savings']:.2f}")
        print(f"  Yearly savings:      ${ca['yearly_savings']:.2f}")
        print()
        
        # Recommendations
        print(f"{'='*70}")
        print("INSIGHTS")
        print(f"{'='*70}\n")
        
        if mp['success_rate'] >= 70:
            print("✓ MoviePy performing well! Excellent cost optimization.")
        elif mp['success_rate'] >= 50:
            print("! MoviePy success rate could be improved. Check common failure causes.")
        else:
            print("✗ MoviePy success rate is low. Consider investigating issues.")
        
        if mp['percentage_of_total'] >= 60:
            print(f"✓ Great balance! {mp['percentage_of_total']:.0f}% of videos using free MoviePy.")
        else:
            print(f"! Only {mp['percentage_of_total']:.0f}% videos using free MoviePy. Could optimize further.")
        
        print()


def main():
    """CLI for intelligent video router."""
    parser = argparse.ArgumentParser(
        description="Intelligent video router with automatic method selection"
    )
    
    # Video generation arguments
    parser.add_argument('--images', help='Comma-separated list of image URLs')
    parser.add_argument('--headline', default='Transform Your Body', help='Headline text')
    parser.add_argument('--cta', default='Start Your Journey', help='CTA text')
    parser.add_argument('--duration', type=float, default=15.0, help='Video duration in seconds')
    parser.add_argument('--music', default='energetic', help='Background music style')
    parser.add_argument('--force', choices=['moviepy', 'creatomate'], help='Force specific method')
    
    # Statistics argument
    parser.add_argument('--stats', action='store_true', help='Show usage statistics')
    parser.add_argument('--days', type=int, default=30, help='Days to analyze for stats')
    
    args = parser.parse_args()
    
    router = IntelligentVideoRouter()
    
    # Show statistics
    if args.stats:
        router.print_statistics(days=args.days)
        sys.exit(0)
    
    # Generate video
    if not args.images:
        print("Error: --images required for video generation")
        print("Use --stats to view statistics instead")
        sys.exit(1)
    
    image_urls = [url.strip() for url in args.images.split(',')]
    
    result = router.create_video(
        image_urls=image_urls,
        headline=args.headline,
        cta_text=args.cta,
        duration=args.duration,
        music_style=args.music,
        force_method=args.force
    )
    
    if result.get('success'):
        print(f"\n{'='*70}")
        print("VIDEO GENERATION COMPLETE!")
        print(f"{'='*70}")
        print(f"Method: {result.get('method', 'unknown')}")
        print(f"Cost: ${result.get('cost', 0):.2f}")
        print(f"Video: {result.get('video_path') or result.get('video_url')}")
        sys.exit(0)
    else:
        print(f"\n✗ Video generation failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()