#!/bin/bash
# Simple wrapper script to generate weekly digest

# Default values
DAYS=7
MIN_UNITS=2
OUTPUT_DIR="digests"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --days)
      DAYS="$2"
      shift 2
      ;;
    --min-units)
      MIN_UNITS="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --days N          Number of days to look back (default: 7)"
      echo "  --min-units N     Minimum number of units (default: 2)"
      echo "  --output-dir DIR  Output directory (default: digests)"
      echo "  --help            Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Generate filename with current date
DATE=$(date +%Y-%m-%d)
OUTPUT_FILE="$OUTPUT_DIR/$DATE.md"

# Run the digest generator
echo "Generating digest for the last $DAYS days (min $MIN_UNITS units)..."
python3 generate_digest.py --days "$DAYS" --min-units "$MIN_UNITS" --output "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
  echo ""
  echo "✓ Digest generated successfully: $OUTPUT_FILE"
  echo ""
  echo "You can now:"
  echo "  - View the digest: cat $OUTPUT_FILE"
  echo "  - Copy for Substack: cat $OUTPUT_FILE | pbcopy  (macOS)"
  echo "  - Copy for Substack: cat $OUTPUT_FILE | xclip -selection clipboard  (Linux)"
else
  echo "✗ Error generating digest"
  exit 1
fi
