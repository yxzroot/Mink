#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [[ ! -f "$PROJECT_ROOT/mink/__main__.py" ]]; then
    printf 'mink: run install.sh from a valid Mink project checkout\n' >&2
    exit 1
fi
BIN_DIR="${HOME}/.local/bin"
LAUNCHER="${BIN_DIR}/mink"

mkdir -p "$BIN_DIR"

{
    printf '%s\n' '#!/usr/bin/env bash'
    printf 'MINK_ROOT=%q\n' "$PROJECT_ROOT"
    cat <<'EOF'
if [[ ! -f "$MINK_ROOT/mink/__main__.py" ]]; then
    printf 'mink: installation no longer exists at %s\n' "$MINK_ROOT" >&2
    exit 1
fi
export MINK_ROOT
if [[ -n "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="$MINK_ROOT:$PYTHONPATH"
else
    export PYTHONPATH="$MINK_ROOT"
fi
exec python3 -m mink "$@"
EOF
} > "$LAUNCHER"
chmod 755 "$LAUNCHER"

case ":${PATH}:" in
    *":${BIN_DIR}:"*) ;;
    *) printf 'mink installed at %s\n' "$LAUNCHER"
       printf 'Add it to your current shell with: export PATH="$HOME/.local/bin:$PATH"\n' ;;
esac

if command -v fish >/dev/null 2>&1; then
    if ! fish -c 'contains -- "$HOME/.local/bin" $fish_user_paths' >/dev/null 2>&1; then
        fish -c 'fish_add_path -U "$HOME/.local/bin"'
        printf 'Added %s to fish PATH.\n' "$BIN_DIR"
    fi
fi

printf 'Mink is ready. Start it from anywhere with: mink start\n'
