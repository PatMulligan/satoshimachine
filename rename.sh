#!/usr/bin/env bash

# Usage: ./rename-plugin.sh oldname newname [extension]
# Example: ./rename-plugin.sh dca_admin mysuperplugin txt

set -euo pipefail

OLD_NAME="$1"
NEW_NAME="$2"
EXTENSION="${3:-*}" # Optional: only rename specific extensions

# 1. Rename files named oldname.ext -> newname.ext
find . -type f -name "${OLD_NAME}.${EXTENSION}" | while read -r file; do
  dir=$(dirname "$file")
  ext="${file##*.}"
  new_path="$dir/${NEW_NAME}.${ext}"
  mv "$file" "$new_path"
  echo "Renamed file: $file -> $new_path"
done

# 2. Replace all occurrences inside all files (safe with null-terminated args)
echo "Replacing content inside files..."
find . -type f -print0 | xargs -0 sed -i "s/${OLD_NAME}/${NEW_NAME}/g"

# 3. Rename templates/dca_admin -> templates/mysuperplugin
if [ -d "templates/${OLD_NAME}" ]; then
  mv "templates/${OLD_NAME}" "templates/${NEW_NAME}"
  echo "Renamed folder: templates/${OLD_NAME} -> templates/${NEW_NAME}"
fi

echo "✅ Done."
