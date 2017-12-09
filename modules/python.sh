#!/usr/bin/env bash

echo "You should run brew info pyenv and read the caveats about putting the eval() in your profile"
eval "$(pyenv init -)"

#Apple has deprecated use of OpenSSL in favor of its own TLS and crypto libraries openssl is
#not symlinked to /usr/local. Include flags
CFLAGS="-I$(brew --prefix openssl)/include" \
LDFLAGS="-L$(brew --prefix openssl)/lib" \

pyenv install 2.7.12
pyenv global 2.7.12
pyenv install 3.6.0
