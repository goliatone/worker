#!/usr/bin/env bash

echo "Get oh-my-zsh..."
sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"

mkdir -p ~/.oh-my-zsh/custom/themes
git clone https://github.com/geometry-zsh/geometry ~/.oh-my-zsh/custom/themes/

echo "Installing patched fonst for consoles..."
pushd /tmp
# clone
git clone https://github.com/powerline/fonts.git --depth=1
# install
cd fonts
./install.sh
# clean-up a bit
popd