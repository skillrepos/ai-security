#!/bin/bash

# Setup script for Groq API key configuration.
# Labs 2 and 3 use the key automatically when it is set; everything else
# in this course is unaffected. With no key, the labs fall back to Ollama.

if [ -n "$1" ]; then
  KEY="$1"
else
  read -rp "Enter your Groq API key: " KEY
fi

if [ -z "$KEY" ]; then
  echo "Error: No key provided. Exiting."
  exit 1
fi

# Set for current terminal
export GROQ_API_KEY="$KEY"

# Set for all future terminals (avoid duplicates)
grep -q "^export GROQ_API_KEY=" ~/.bashrc 2>/dev/null && \
  sed -i "s|^export GROQ_API_KEY=.*|export GROQ_API_KEY=$KEY|" ~/.bashrc || \
  echo "export GROQ_API_KEY=$KEY" >> ~/.bashrc

echo "Done! GROQ_API_KEY is set. Labs 2 and 3 will now use Groq."
