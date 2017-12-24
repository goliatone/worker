# Welcome to worker! [![Build Status](https://travis-ci.org/thibmaek/worker.svg?branch=master)](https://travis-ci.org/thibmaek/worker)
> Getting your macOS machine up and running!

Worker is a personal project to quickly get new or clean installed macOS machines
up and running with everything I need for my development workflow.

It currently presets all of the following:
* [macOS sensible defaults](https://github.com/mathiasbynens/dotfiles/blob/master/.macos)
* [Brew](https://github.com/Homebrew/homebrew) (with casks)
* Node (trough [nvm](https://github.com/creationix/nvm)) (with global packages trough yarn)
* Go (through [gvm]())
* Docker (through [dvm]() and [docker-toolbox]())
* Ruby (trough [rbenv](https://github.com/rbenv/rbenv))
* Python (trough [pyenv](https://github.com/yyuu/pyenv))
* [Atom](https://github.com/atom/atom) (with apm packages & themes)

This is great for setting up the tools you need.

### Installing
Just running it from the top is easy:

```shell
git clone https://github.com/goliatone/worker.git .worker && cd .worker
./make
```

`make` is the file that points your shell to each specific module.
If you want to turn certain modules of, just comment them out from `make`

If you want to you can also install this on a file-per-file base, just run the .sh files inside of the modules directory. The extensions directory installs additional content to the modules.


##

```
curl -LOk https://github.com/goliatone/worker/archive/v0.1.zip
unzip v0.1.zip
mv worker* worker
```

#### TODO
- [x] Ask for password once when we run script
- [x] Ensure that rbenv has right permissions
- [ ] dotfiles
  - [ ] reminder about `ssh-add`
