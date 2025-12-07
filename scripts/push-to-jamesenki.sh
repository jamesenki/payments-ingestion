#!/bin/bash
# Script to push to jamesenki GitHub repository using a token

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Push to jamesenki/payments-ingestion"
echo "=========================================="
echo ""

# Check if token is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <GITHUB_TOKEN>${NC}"
    echo ""
    echo "Example:"
    echo "  $0 ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    echo ""
    echo "Or set as environment variable:"
    echo "  export GITHUB_TOKEN=your_token"
    echo "  $0"
    echo ""
    exit 1
fi

# Use provided token or environment variable
GITHUB_TOKEN=${1:-$GITHUB_TOKEN}

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: GitHub token is required${NC}"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${GREEN}Current branch: ${CURRENT_BRANCH}${NC}"
echo ""

# Check if repository exists on GitHub
echo "Checking if repository exists..."
REPO_URL="https://api.github.com/repos/jamesenki/payments-ingestion"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token ${GITHUB_TOKEN}" "$REPO_URL")

if [ "$HTTP_CODE" == "404" ]; then
    echo -e "${YELLOW}⚠️  Repository doesn't exist yet on GitHub${NC}"
    echo ""
    echo "Please create it first:"
    echo "  1. Go to https://github.com/new"
    echo "  2. Repository name: payments-ingestion"
    echo "  3. Choose public or private"
    echo "  4. DO NOT initialize with README, .gitignore, or license"
    echo "  5. Click 'Create repository'"
    echo ""
    read -p "Press Enter after you've created the repository, or Ctrl+C to cancel..."
elif [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}Error: Failed to check repository (HTTP $HTTP_CODE)${NC}"
    echo "Please verify your token has the correct permissions"
    exit 1
else
    echo -e "${GREEN}✅ Repository exists${NC}"
fi

echo ""
echo "Pushing to jamesenki/payments-ingestion..."
echo ""

# Push using token
if git push https://${GITHUB_TOKEN}@github.com/jamesenki/payments-ingestion.git ${CURRENT_BRANCH}; then
    echo ""
    echo -e "${GREEN}✅ Successfully pushed to jamesenki/payments-ingestion!${NC}"
    echo ""
    echo "Repository URL: https://github.com/jamesenki/payments-ingestion"
    echo ""
    
    # Update remote URL (without token for future use)
    git remote set-url jamesenki https://github.com/jamesenki/payments-ingestion.git
    echo -e "${GREEN}✅ Remote 'jamesenki' configured${NC}"
    echo ""
    echo "To push in the future, you can use:"
    echo "  git push jamesenki ${CURRENT_BRANCH}"
    echo ""
    echo "Note: You'll need to authenticate using:"
    echo "  - GitHub CLI (gh auth login)"
    echo "  - SSH key"
    echo "  - Personal Access Token"
else
    echo ""
    echo -e "${RED}❌ Push failed${NC}"
    exit 1
fi

