#!/bin/bash
echo "Cleaning Python environment..."

# Get all installed packages except essentials
pip list --format=freeze | grep -v "^pip=" | grep -v "^setuptools=" | grep -v "^wheel=" | awk -F'==' '{print $1}' > /tmp/installed.txt

# Get packages from requirements.txt
sed 's/>=.*//' requirements.txt | grep -v '^$' > /tmp/required.txt

# Find packages to uninstall (installed but not required)
grep -v -f /tmp/required.txt /tmp/installed.txt > /tmp/to_uninstall.txt

# Show what will be uninstalled
echo "Packages to uninstall ($(wc -l < /tmp/to_uninstall.txt) total):"
head -20 /tmp/to_uninstall.txt

if [ $(wc -l < /tmp/to_uninstall.txt) -gt 0 ]; then
    echo
    echo "Proceeding with uninstallation..."
    # Uninstall all at once for speed
    cat /tmp/to_uninstall.txt | xargs pip uninstall -y
else
    echo "No packages to uninstall."
fi

echo
echo "Installing packages from requirements.txt..."
pip install -r requirements.txt

echo
echo "Clean installation complete!"
echo "Installed packages:"
pip list | grep -E "(ollama|google-genai|langchain|chromadb|pydantic|pytest)"