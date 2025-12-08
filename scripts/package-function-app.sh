#!/bin/bash
#
# Package Function App for Deployment
#
# Creates a deployment-ready zip package containing:
# - Function App code
# - Dependencies
# - Configuration files
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default values
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_ROOT/deploy_packages}"
ENVIRONMENT="${1:-dev}"
VERSION="${2:-$(git rev-parse --short HEAD 2>/dev/null || echo "local")}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "Function App Packaging"
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo "========================================"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"
PACKAGE_DIR="$OUTPUT_DIR/function-app-$ENVIRONMENT-$VERSION"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

echo -e "${BLUE}📦 Creating deployment package...${NC}"

# Copy function app code
echo "Copying function app code..."
cp -r "$PROJECT_ROOT/src/function_app" "$PACKAGE_DIR/"

# Copy requirements
echo "Copying requirements..."
cp "$PROJECT_ROOT/requirements.txt" "$PACKAGE_DIR/"

# Copy function.json if exists
if [ -f "$PROJECT_ROOT/src/function_app/function.json" ]; then
    cp "$PROJECT_ROOT/src/function_app/function.json" "$PACKAGE_DIR/"
fi

# Create host.json if it doesn't exist
if [ ! -f "$PACKAGE_DIR/host.json" ]; then
    echo "Creating host.json..."
    cat > "$PACKAGE_DIR/host.json" <<EOF
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 20
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
EOF
fi

# Install dependencies
echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip --quiet
pip install -r "$PROJECT_ROOT/requirements.txt" \
    --target "$PACKAGE_DIR/.python_packages/lib/python3.11/site-packages" \
    --quiet

# Create deployment zip
echo "Creating deployment zip..."
cd "$PACKAGE_DIR"
ZIP_FILE="$OUTPUT_DIR/function-app-$ENVIRONMENT-$VERSION.zip"
zip -r "$ZIP_FILE" . \
    -x "*.pyc" "__pycache__/*" "*.git*" "*.pyc" "*.pyo" "*.pyd" \
    > /dev/null

cd "$PROJECT_ROOT"

# Display package info
echo ""
echo -e "${GREEN}✅ Package created successfully!${NC}"
echo "Package: $ZIP_FILE"
echo "Size: $(du -h "$ZIP_FILE" | cut -f1)"
echo ""
echo "Package contents:"
unzip -l "$ZIP_FILE" | head -20
echo ""

