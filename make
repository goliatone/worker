#!/usr/bin/env bash

#####################################################
# To start worker, run this file
#
# You can turn off modules & extensions by commenting
# out the lines below the echo's
################################

# Export env ROOT to current directory run test from absolute path
ROOT=$PWD

# Make sure we can execute each file
for MODULE in $ROOT/modules/*; do chmod +x $MODULE; done

# 1. Install Command Line Tools.
echo "Updating xcode-select..."
xcode-select --install;

# 2. Install homebrew.
echo "Installing brew..."
bash "$ROOT/modules/brew.sh"

# 3. Install formulas and cask from Brewfile.
echo "Reading from brewfile..."
brew bundle --file="$ROOT/extensions/Brewfile"

# 4. Install Node and NPM trough NVM.
echo "Downloading and installing nvm..."
bash "$ROOT/modules/nvm.sh"

# 5. Installing yarn and global packages
echo "Installing yarn..."
bash "$ROOT/extensions/yarn"

# 6. Install Python versions for pyenv.
echo "Installing pyenv versions..."
bash "$ROOT/modules/python.sh"

echo "Installing modules from pip..."
bash "$ROOT/extensions/pip"

# 7. Use the .gemrc file for Rubygems
echo "Presetting Ruby..."
bash "$ROOT/modules/ruby.sh"

# 8. Install Rubygems.
echo "Installing some gems..."
bundle install --gemfile="$ROOT/extensions/Gemfile"

# 9. Install APM packages & themes
echo "Installing apm packages..."
apm install --packages-file "$ROOT/extensions/Atomfile"

# 10. Use the .gemrc file for Rubygems
echo "Installing gvm to manage Go..."
bash "$ROOT/modules/gvm.sh"

# 11. Update macOS defaults
echo "Updating macOS defaults..."
bash "$ROOT/modules/mac.sh"

# 12. Updte vim...
echo "Installing vim..."
bash "$ROOT/modules/vim.sh"

echo "Configure iterm2..."
bash "$ROOT/modules/iterm2.sh"

echo "Configure zsh..."
bash "$ROOT/modules/zsh.sh"

# 14. Perform additional local changes described in ./worker.local
if [[ -f "$ROOT/worker.local" ]]; then bash "$ROOT/worker.local"; fi

# Reload modified applications
for APP in "Activity Monitor" "Address Book" "Calendar" "Contacts" "cfprefsd" \
"Dock" "Finder" "Mail" "Messages" "Safari" "SystemUIServer"; do
	killall "${APP}" > /dev/null 2>&1
done

echo "Done. Note that some of these changes require a logout/restart to take effect."
echo "Now reloading shell..."
exec $SHELL -l
