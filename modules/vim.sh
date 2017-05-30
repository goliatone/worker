#!/usr/bin/env bash

# Clone Vundle
echo "Installing Vundle..."
git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim

echo "Running Vundle install..."
vim +PluginInstall +qall
