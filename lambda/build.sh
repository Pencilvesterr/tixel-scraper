#!/bin/bash
set -e

# Clean previous builds
rm -rf dist
rm -rf package
rm -f requirements.txt

# Generate requirements.txt from Poetry
poetry export -f requirements.txt --without-hashes > requirements.txt

# Create necessary directories
mkdir -p dist
mkdir -p package

# Install dependencies into the package directory
cd package
pip install \
    -r ../requirements.txt \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    --target .

# Go back to main directory
cd ..

# Copy our Lambda code
cp *.py package/

# Create deployment package (from the package directory to maintain correct structure)
cd package
zip -r ../dist/lambda.zip ./*
cd ..

# Clean up
rm -rf package
# rm -f requirements.txt

echo "Build complete! Deployment package is at dist/lambda.zip"
