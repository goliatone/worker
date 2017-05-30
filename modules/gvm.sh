#!/usr/bin/env bash

brew update
brew install mercurial

# Create .bash_profile if it doesn't exist
if [[ ! -f ~/.bash_profile ]]; then touch ~/.bash_profile; fi

# Directly source it to .bash_profile trought the pipe to bash
curl -o- https://raw.githubusercontent.com/moovweb/gvm/master/binscripts/gvm-installer | PROFILE=~/.bash_profile bash
