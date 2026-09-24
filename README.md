# Mink

Mink is a tiny animated terminal companion and lightweight Linux music
controller. It lives in a private tmux split, so the shell next to it stays a
real shell.

## Version 0.1.2

This release adds a responsive music panel, configurable themes and behavior,
more pet moods, optional system status, and reliable mouse-wheel protection.

## Features

- Responsive pet and music layout for small laptop panes and wide terminals.
- Song, artist, playback state, progress, and timing from `playerctl`.
- Clean offline fallback when no player or metadata is available.
- Data-driven idle, blink, sleepy, sleeping, waking, happy, excited, annoyed,
  surprised, looking-around, stretching, dancing, eating, drinking, playing,
  love, and goodbye animation sequences.
- Catppuccin Mocha, Tokyo Night, Dracula, Nord, Forest, Sunset, and default
  Mink themes.
- Optional status bar with song, uptime, CPU load, RAM, hostname, and version.
- Mouse wheel over Mink never enters tmux copy mode or terminal scrollback.
- No Python dependencies beyond the standard library.

## Install and launch

Requirements:

- Linux
- Python 3.9+
- tmux
- Optional: `playerctl` and an MPRIS-compatible music player

```sh
git clone https://github.com/yxzroot/Mink.git
cd Mink
./install.sh
mink start
```

Use `mink close` to stop the private session cleanly. `mink --version` prints
the installed version.

## Controls

Commands control the music player from the shell:

```sh
mink play
mink pause
mink toggle
mink next
mink prev
mink volume 80
mink status
mink close
```

When the Mink pane has focus, `h` or Space makes the pet happy, `a` makes it
annoyed, `e` makes it excited, and `w` starts a waking reaction. Clicking the
pet also creates a small happy reaction. Wheel input is consumed and does not
scroll terminal history.

## Configuration

Mink works without a config file. Optional JSON configuration lives at:

```text
~/.config/mink/config.json
```

Set `MINK_CONFIG` to use another path. Environment variables override JSON
values. Available settings include:

```json
{
  "theme": "catppuccin-mocha",
  "sleep_after": 22,
  "tick_interval": 0.08,
  "animation_speed": 1.0,
  "poll_interval": 1,
  "animation": true,
  "random_idle": true,
  "music_visible": true,
  "status_bar": true,
  "status_items": "song,uptime,hostname",
  "layout": "auto",
  "startup_animation": true
}
```

`layout` may be `auto`, `stacked`, or `columns`. Invalid values safely use
defaults. The equivalent environment overrides are `MINK_THEME`,
`MINK_SLEEP_AFTER`, `MINK_TICK_INTERVAL`, `MINK_POLL_INTERVAL`,
`MINK_ANIMATION_SPEED`, `MINK_RANDOM_IDLE`,
`MINK_ANIMATION`, `MINK_MUSIC_VISIBLE`, `MINK_STATUS_BAR`,
`MINK_STATUS_ITEMS`, `MINK_LAYOUT`, and `MINK_STARTUP_ANIMATION`.

## Development

```sh
python3 -m unittest discover -s tests -v
python3 -m mink --direct
```

The UI uses one lightweight loop, redraws only on its animation cadence, polls
music once per second, and restores terminal state through `curses.wrapper`.
