#!/usr/bin/env bash

# Comment out installations/setups you dont want
# Run this file by running ./make in the shell

# Nicer log output
fancy_echo() {
  local fmt="$1"; shift
  printf "\n$fmt\n" "$@ \e[0m"
}

# Export env ROOT to current directory run test from absolute path
ROOT=$PWD

# 1. Run OS X modifications.
fancy_echo "Presetting macOS..."
. "$ROOT/modules/macos.sh"

# 2. Install Command Line Tools.
fancy_echo "Installing xcode-select..."
. "$ROOT/modules/xcode.sh"

# 3. Install homebrew.
fancy_echo "Installing brew..."
. "$ROOT/modules/brew.sh"

# 4. Install formulas and cask from Brewfile.
fancy_echo "Reading from brewfile..."
brew bundle --file="$ROOT/extensions/Brewfile"

# 5. Install Node and NPM trough NVM.
fancy_echo "Downloading and installing nvm..."
. "$ROOT/modules/nvm.sh"

# 6. Install global node modules.
fancy_echo "Installing node modules..."
. "$ROOT/extensions/npm"

# 7. Install Python versions for pyenv.
fancy_echo "Installing pyenv versions..."
. "$ROOT/modules/python.sh"

fancy_echo "Installing modules from pip..."
. "$ROOT/extensions/pip"

# 8. Use the .gemrc file for Rubygems
fancy_echo "Presetting Ruby..."
. "$ROOT/modules/Ruby.sh"

# 9. Install Rubygems.
fancy_echo "Installing some gems..."
. "$ROOT/extensions/ruby.sh"

# 10. Install APM packages & themes
fancy_echo "Installing apm packages..."
apm install --packages-file "$ROOT/extensions/Atomfile"

# 11. Perform additional local changes described in ~/.worker.local
. "$ROOT/worker.local"

# Reload modified applications
for APP in "Activity Monitor" "Address Book" "Calendar" "Contacts" "cfprefsd" \
"Dock" "Finder" "Mail" "Messages" "Safari" "SystemUIServer" \
"Transmission" "Twitter"; do
	killall "${APP}" > /dev/null 2>&1
done

fancy_echo "Done. Note that some of these changes require a logout/restart to take effect."
fancy_echo "Now reloading shell..."
exec $SHELL -l
