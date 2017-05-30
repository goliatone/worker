#!/usr/bin/env bash

# 1. Check if xcode tools are installed and install brew
if which xcode-select >/dev/null; then
  ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
  brew doctor
else
  echo "Command line tools not installed!" && exit 1
fi

# 2. Disable analytics
# Create .bash_profile if it doesn't exist
if [[ ! -f ~/.bash_profile ]]; then touch ~/.bash_profile; fi
echo 'export HOMEBREW_ANALYTICS_DEBUG=1' >> ~/.bash_profile
# Also, just tell brew to not care about what we do...
if which brew > /dev/null; then
  brew analytics off
fi


# 3. Tap boneyard for Brewfile support
if which brew > /dev/null; then
  brew tap Homebrew/bundle
else
  echo "brew not installed/found!" && exit 1
fi
