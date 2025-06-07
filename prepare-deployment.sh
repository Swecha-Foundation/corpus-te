#!/bin/bash

# Prepare deployment package for Hetzner VM
# This script creates a deployment package with all necessary files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${YELLOW}==> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Configuration
DOCKER_IMAGE_NAME="corpus-te-app"
PACKAGE_NAME="corpus-te-deploy-$(date +%Y%m%d_%H%M%S)"

echo -e "${GREEN}Preparing Corpus TE deployment package...${NC}"

# Check if required files exist
REQUIRED_FILES=(
    "docker-compose.prod.yml"
    "deploy.sh"
    "setup-server.sh"
    ".env.example"
    "Dockerfile"
    "HETZNER_DEPLOYMENT_GUIDE.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file missing: $file"
        exit 1
    fi
done

# Build Docker image
print_step "Building Docker image..."
if docker build -t $DOCKER_IMAGE_NAME .; then
    print_success "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Save Docker image
print_step "Saving Docker image..."
docker save $DOCKER_IMAGE_NAME > $DOCKER_IMAGE_NAME.tar
print_success "Docker image saved as $DOCKER_IMAGE_NAME.tar"

# Create deployment package
print_step "Creating deployment package..."
mkdir -p $PACKAGE_NAME

# Copy files to package directory
cp docker-compose.prod.yml $PACKAGE_NAME/
cp deploy.sh $PACKAGE_NAME/
cp setup-server.sh $PACKAGE_NAME/
cp .env.example $PACKAGE_NAME/
cp HETZNER_DEPLOYMENT_GUIDE.md $PACKAGE_NAME/
cp $DOCKER_IMAGE_NAME.tar $PACKAGE_NAME/

# Make scripts executable
chmod +x $PACKAGE_NAME/deploy.sh
chmod +x $PACKAGE_NAME/setup-server.sh

# Create deployment instructions
cat > $PACKAGE_NAME/README.md << 'EOF'
# Corpus TE Deployment Package

This package contains everything needed to deploy Corpus TE to a Hetzner VM.

## Quick Start

1. **Upload this package to your server**:
   ```bash
   scp -r corpus-te-deploy-* user@your-server-ip:~/
   ```

2. **On the server, run the setup script first** (one-time setup):
   ```bash
   cd corpus-te-deploy-*
   ./setup-server.sh
   sudo reboot
   ```

3. **After reboot, configure and deploy**:
   ```bash
   cd corpus-te-deploy-*
   cp .env.example .env
   nano .env  # Edit with your configuration
   ./deploy.sh
   ```

## Files Included

- `docker-compose.prod.yml` - Production Docker Compose configuration
- `deploy.sh` - Deployment script
- `setup-server.sh` - Server setup script (run once)
- `.env.example` - Environment configuration template
- `corpus-te-app.tar` - Docker image
- `HETZNER_DEPLOYMENT_GUIDE.md` - Detailed deployment guide

## Important Notes

- Update the `.env` file with your secure passwords and configuration
- Make sure to open necessary firewall ports
- Consider setting up SSL certificates for production use
- Review the detailed deployment guide for advanced configuration

For detailed instructions, see `HETZNER_DEPLOYMENT_GUIDE.md`.
EOF

# Create archive
print_step "Creating deployment archive..."
tar -czf $PACKAGE_NAME.tar.gz $PACKAGE_NAME
print_success "Deployment package created: $PACKAGE_NAME.tar.gz"

# Clean up temporary files
rm -rf $PACKAGE_NAME
rm $DOCKER_IMAGE_NAME.tar

# Calculate package size
PACKAGE_SIZE=$(du -sh $PACKAGE_NAME.tar.gz | cut -f1)

echo -e "${GREEN}"
echo "=============================================="
echo "  Deployment Package Ready!"
echo "=============================================="
echo "Package: $PACKAGE_NAME.tar.gz"
echo "Size: $PACKAGE_SIZE"
echo ""
echo "To deploy to your Hetzner VM:"
echo "1. Upload: scp $PACKAGE_NAME.tar.gz user@your-server-ip:~/"
echo "2. Extract: tar -xzf $PACKAGE_NAME.tar.gz"
echo "3. Setup: cd $PACKAGE_NAME && ./setup-server.sh"
echo "4. Reboot: sudo reboot"
echo "5. Deploy: ./deploy.sh"
echo -e "${NC}"

print_success "Deployment package preparation completed!"
