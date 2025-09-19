"""
Main entry point for IntelliRadar crawler
"""

import argparse
from crawler.pipeline import CrawlerPipeline


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='IntelliRadar Threat Intelligence Crawler')
    parser.add_argument(
        '--sources', 
        nargs='+', 
        help='Specific sources to crawl. Available: qianxin, datadoghq, rhisac, checkpoint, phylum, securityaffairs',
        default=None
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=3,
        help='Number of concurrent workers (default: 3)'
    )
    
    args = parser.parse_args()
    
    # Create and run pipeline
    pipeline = CrawlerPipeline()
    
    if args.sources:
        # Run specific sources
        results = pipeline.run_sources(args.sources, args.workers)
    else:
        # Run all sources
        results = pipeline.run_all(args.workers)
    
    # Print summary
    print("\n" + "="*50)
    print("CRAWLER SUMMARY")
    print("="*50)
    
    for result in results:
        status_icon = "✓" if result.get('status') == 'success' else "✗"
        source = result.get('source', 'unknown')
        
        if result.get('status') == 'success':
            links = result.get('links_found', 0)
            duration = result.get('duration', 0)
            print(f"{status_icon} {source:<15} {links:>3} links ({duration:.1f}s)")
        else:
            error = result.get('error', 'unknown error')
            print(f"{status_icon} {source:<15} Error: {error}")
    
    print("="*50)


if __name__ == '__main__':
    main()
