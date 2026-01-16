#!/bin/bash
# Sync shared code to all Lambda directories

echo "🔄 Syncing shared code to all Lambda functions..."

for lambda_dir in src/lambdas/*/; do
    lambda_name=$(basename "$lambda_dir")
    echo "  → Syncing to $lambda_name"
    
    # Remove old shared directory
    rm -rf "$lambda_dir/shared"
    
    # Copy fresh shared code
    cp -r src/shared "$lambda_dir/"
done

echo "✅ Sync complete!"
echo ""
echo "Next steps:"
echo "1. sam build"
echo "2. sam deploy"
