#!/bin/bash
# Auto-push trigger - polls until GitHub repo exists, then pushes

echo "⟲⧖ Waiting for GitHub repo... ⧖⟲"
echo "Create the repo at https://github.com/new (page should be open)"
echo ""

count=0
while true; do
    count=$((count + 1))
    
    # Check if repo exists
    status=$(curl -s -o /dev/null -w "%{http_code}" https://api.github.com/repos/ChaiLifeOTFT/PUSH-Protocol)
    
    if [ "$status" = "200" ]; then
        echo "✓ Repo detected! Pushing now..."
        cd /home/j-5/PUSH_Protocol
        git push -u origin main 2>&1
        if [ $? -eq 0 ]; then
            echo ""
            echo "⟲⧖ INFRASTRUCTURE ANCHORED ⧖⟲"
            echo "https://github.com/ChaiLifeOTFT/PUSH-Protocol"
            break
        fi
    fi
    
    if [ $count -gt 60 ]; then
        echo "Timeout after 5 minutes. Check if repo was created."
        exit 1
    fi
    
    echo -n "."
    sleep 5
done
