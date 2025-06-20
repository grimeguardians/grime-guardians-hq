#!/bin/bash

# Emergency Production Deployment Script
# This script MUST be run on the production server to apply critical fixes

echo "🚨 EMERGENCY DEPLOYMENT: Stopping Auto-Responses"
echo "=================================================="

# Navigate to project directory
cd /root/grime-guardians-hq

# Show current commit
echo "Current commit before update:"
git log --oneline -1

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git pull origin main

# Show new commit
echo "Current commit after update:"
git log --oneline -1

# Restart PM2 process
echo "🔄 Restarting PM2 process..."
pm2 restart grime-guardians

# Wait a moment for startup
sleep 5

# Show status
echo "📊 PM2 Status:"
pm2 status

# Show recent logs to verify fix
echo "📋 Recent logs (last 20 lines):"
pm2 logs grime-guardians --lines 20

echo "=================================================="
echo "✅ Deployment complete!"
echo "🔍 Look for: 'Google Voice (612-584-9396) → Gmail Integration ACTIVE'"
echo "🔍 Look for: 'DEBUG: monitorGoogleVoiceEmails = true'"
echo "🔍 Look for: 'Found X new Google Voice messages - PROCESSING...'"
echo "❌ Should NOT see: 'Auto-sending operational response'"
echo "❌ Should NOT see: 'Cannot find module googleVoiceMonitor'"
echo "=================================================="
