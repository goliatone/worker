#!/usr/bin/env bash

eval "$(rbenv init -)"

# Export rbenv 
echo 'eval "$(rbenv init - --no-rehash)"' >> ~/.bash_profile
# Using rbenv over macOS pre-installed Ruby in Brewfile
rbenv init

rbenv install 2.3.1
rbenv global 2.3.1

gem install bundler
gem install bundler_bash_completion
