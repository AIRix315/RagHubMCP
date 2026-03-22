#!/bin/bash
# RagHubMCP Build Script for Linux/macOS
# Go + PyInstaller hybrid packaging

set -e

echo "================================================"
echo "  RagHubMCP Build Script (Unix)"
echo "================================================"
echo

# Get version from version.txt
VERSION=$(cat ../version.txt 2>/dev/null || echo "0.0.0")
echo "Version: $VERSION"

# Build timestamp
BUILD_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo "Build Time: $BUILD_TIME"

# Detect OS
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

echo "Platform: $OS $ARCH"
echo

# Check prerequisites
echo "Checking prerequisites..."

# Check Go
if ! command -v go &> /dev/null; then
    echo "ERROR: Go not found. Please install Go 1.21+"
    exit 1
fi
echo "[OK] Go found: $(go version)"

# Check Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python not found. Please install Python 3.11+"
        exit 1
    fi
    PYTHON_CMD=python
else
    PYTHON_CMD=python3
fi
echo "[OK] Python found: $($PYTHON_CMD --version)"

# Check PyInstaller
if ! $PYTHON_CMD -m pip show pyinstaller &> /dev/null; then
    echo "WARNING: PyInstaller not found. Installing..."
    $PYTHON_CMD -m pip install pyinstaller
fi
echo "[OK] PyInstaller ready"

echo
echo "================================================"
echo "  Step 1: Building Frontend"
echo "================================================"
echo

cd ../frontend
if [ $? -ne 0 ]; then
    echo "ERROR: Cannot find frontend directory"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Build frontend
echo "Building Vue frontend..."
npm run build
if [ $? -ne 0 ]; then
    echo "ERROR: Frontend build failed"
    exit 1
fi

echo "[OK] Frontend built successfully"
cd ../pack

echo
echo "================================================"
echo "  Step 2: Preparing Embed Resources"
echo "================================================"
echo

cd go

# Create embed directories in pack/go/
mkdir -p frontend backend data

# Copy frontend dist to pack/go/frontend/dist
echo "Copying frontend dist..."
if [ -d "../../frontend/dist" ]; then
    rm -rf frontend/dist
    cp -r ../../frontend/dist frontend/
    echo "[OK] Frontend copied to pack/go/frontend/dist"
else
    echo "[WARN] Frontend dist not found, creating placeholder"
    touch frontend/.gitkeep
fi

# Copy backend source to pack/go/backend/
echo "Copying backend source..."
rm -rf backend/src
cp -r ../../backend/src backend/
cp ../../backend/config.yaml backend/
cp ../../backend/pyproject.toml backend/
echo "[OK] Backend copied to pack/go/backend"

# Copy/prepare data directory
echo "Preparing data directory..."
if [ -d "../../data" ]; then
    rm -rf data
    cp -r ../../data data
    echo "[OK] Data copied"
else
    mkdir -p data/flashrank_cache
    mkdir -p data/chroma
    echo "[OK] Data directories created"
fi

# Create placeholder for models download script
if [ ! -f "data/download_models.py" ]; then
    cat > data/download_models.py << 'EOF'
# Download Rerank models on first run
# Models will be downloaded to data/flashrank_cache/
EOF
fi

cd ..

echo
echo "================================================"
echo "  Step 3: Running Go Tests"
echo "================================================"
echo

cd go

echo "Running Go unit tests..."
go test ./... -v -short || echo "WARNING: Some tests failed, but continuing with build"

echo "[OK] Tests completed"

echo
echo "================================================"
echo "  Step 4: Building Go Wrapper"
echo "================================================"
echo

# Download dependencies
echo "Downloading Go dependencies..."
go mod download
go mod tidy

# Build with version info
LDFLAGS="-s -w -X main.version=$VERSION -X main.buildTime=$BUILD_TIME"

# Determine output filename
case "$OS" in
    linux)
        OUTPUT="../../../dist/RHM-linux"
        ;;
    darwin)
        OUTPUT="../../../dist/RHM-macos"
        ;;
    *)
        OUTPUT="../../../dist/RHM-$OS"
        ;;
esac

echo "Building executable..."
go build -ldflags="$LDFLAGS" -o "$OUTPUT" .
if [ $? -ne 0 ]; then
    echo "ERROR: Go build failed"
    exit 1
fi

chmod +x "$OUTPUT"

echo "[OK] Go wrapper built: $(basename $OUTPUT)"
cd ..

echo
echo "================================================"
echo "  Step 5: Building Python Package (Optional)"
echo "================================================"
echo

# This step is optional - the Go wrapper can use system Python
# If you want to embed Python, run this:

# cd python
# $PYTHON_CMD -m PyInstaller RHM.spec --clean
# cd ..

echo
echo "================================================"
echo "  Build Complete!"
echo "================================================"
echo
echo "Output files:"
echo "  - $(dirname $OUTPUT)/$(basename $OUTPUT) (Go wrapper)"
echo "  - pack/go/frontend/  (Frontend embed)"
echo "  - pack/go/backend/   (Backend embed)"
echo "  - pack/go/data/      (Data embed)"
echo

echo "To test:"
echo "  $(dirname $OUTPUT)/$(basename $OUTPUT) --version"
echo "  $(dirname $OUTPUT)/$(basename $OUTPUT) --help"
echo "  $(dirname $OUTPUT)/$(basename $OUTPUT) --no-browser --no-tray"
echo

echo "To run tests:"
echo "  cd pack/go && go test ./... -v"
echo