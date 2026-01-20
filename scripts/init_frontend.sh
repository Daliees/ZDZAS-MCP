#!/bin/bash
# Initialize Vite React + TypeScript frontend for ZAS Admin Dashboard

set -e

FRONTEND_DIR="/home/ryan/code/ZDZAS-MCP/src/zas/dashboard/frontend"

echo "Creating Vite React + TypeScript project..."
cd /home/ryan/code/ZDZAS-MCP/src/zas/dashboard

# Create Vite project with React + TypeScript
npm create vite@latest frontend -- --template react-ts

cd frontend

echo "Installing dependencies..."
npm install

echo "Installing additional packages..."
npm install react-router-dom @tanstack/react-query axios recharts date-fns
npm install -D @types/node

echo "Installing Tailwind CSS..."
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

echo "Frontend initialization complete!"
echo "To start the dev server: cd $FRONTEND_DIR && npm run dev"
