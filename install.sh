#!/bin/bash

# NER Labeler Installation Script
# Extracted from Label Studio NER functionality

set -e

echo "🏷️  NER Labeler Installation"
echo "============================"

# Check Python version
echo "📋 Checking Python version..."
python3 --version || {
    echo "❌ Python 3 is required but not found. Please install Python 3.7+"
    exit 1
}

# Check pip
echo "📦 Checking pip..."
python3 -m pip --version || {
    echo "❌ pip is required but not found. Please install pip for Python 3"
    exit 1
}

# Install dependencies
echo "⬇️  Installing dependencies..."
python3 -m pip install -r requirements_ner.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p static logs

# Set permissions
echo "🔒 Setting permissions..."
chmod +x ner_web_interface.py
chmod +x examples/ner_demo.py
chmod +x tests/test_overlapping_annotations.py

# Run tests
echo "🧪 Running tests..."
python3 tests/test_overlapping_annotations.py

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🚀 Quick Start:"
echo "   python3 ner_web_interface.py"
echo "   Then visit: http://localhost:5001"
echo ""
echo "📚 Documentation:"
echo "   docs/NER_README.md - Detailed documentation"
echo "   docs/NER_EXTRACTION_SUMMARY.md - Korean summary"
echo ""
echo "🎯 Examples:"
echo "   python3 examples/ner_demo.py"
echo ""
echo "Happy Annotating! 🎉"