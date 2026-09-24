# Mink

Mink is a tiny animated terminal companion and lightweight Linux music
controller. It lives in a small tmux pane, so the adjacent pane remains a
normal interactive shell: commands, scrollback, signals, and terminal
programs continue to work normally.

## Download

Clone the public repository and install the global launcher:

```sh
git clone https://github.com/yxzroot/Mink.git
cd Mink
./install.sh
```

After that one-time setup, launch Mink from any directory:

```sh
mink start
```

## Requirements

- Linux
- Python 3.9+
- [tmux](https://github.com/tmux/tmux)
- Optional: `playerctl` and an MPRIS-compatible music player

Arch/CachyOS:

```sh
sudo pacman -S tmux playerctl
```

## Install and run

From a checkout:

```sh
cd ~/Desktop/mink
./install.sh
```

If `~/.local/bin` is not already on the current shell's `PATH`, either open a
new shell or run:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

For fish, use:

```fish
fish_add_path "$HOME/.local/bin"
```

The installer automatically adds this path to fish's persistent user path when
fish is installed. Bash and other shells need a new shell (or the one-line
`export` above) to refresh their current environment.

After setup, start Mink from any directory:

```sh
mink start
```

The installer places one launcher at `~/.local/bin/mink`. The launcher points
to this checkout; it does not copy the project or require pip. `mink start`
opens a private tmux session with your shell above and a compact, borderless
Mink area along the bottom. If Mink is already running,
the command leaves the existing instance alone. Run `mink quit` to close it and
return to the original terminal. The shell pane is intentionally not emulated
by Mink.

Mink does not capture keyboard input from the shell. Control the running
instance from the shell:

```sh
mink play
mink pause
mink toggle
mink next
mink prev
mink volume 80
mink status
mink quit
mink close
```

The pet pane is display-only, so the shell remains completely normal. Use
`mink help` for the complete command list.

If no MPRIS player or `playerctl` is available, Mink remains a useful animated
pet and displays a short offline message.

## Layout and configuration

The pane is deliberately compact. tmux can resize it as usual, and Mink
stacks playback metadata beside or below the pet when the pane is small. The
`MINK_SHELL` environment variable can select the shell used for the session;
otherwise `$SHELL` (or `/bin/sh`) is used.

Mink enables mouse handling only for its private tmux session. Wheel events
over the display pane are consumed without entering tmux copy mode or moving
terminal scrollback; the adjacent shell remains a normal interactive pane.

This first version keeps configuration intentionally small. Future settings
can be added without changing the shell integration because the pet is an
independent tmux pane.

## Development

```sh
python3 -m unittest discover -s tests -v
python3 -m mink --direct   # run inside an existing tmux pane
```

Mink polls playerctl once per second, redraws only its own pane, and restores
the terminal through curses cleanup on exit.

## Credits

I'm a lazy chud so GitHub Copilot pushed the project for me :3
