#!/bin/sh
# SlideMarks for Mac: installs the font, and the Office add-in for Word and PowerPoint.
#
#   Install:    curl -fsSL {{BASE_URL}}/install.sh | sh
#   Uninstall:  curl -fsSL {{BASE_URL}}/install.sh | sh -s uninstall
#
# Everything goes into your own Library folder, so no administrator password is needed:
#   ~/Library/Fonts/SlideMarks-Regular.ttf
#   ~/Library/Containers/com.microsoft.{Word,Powerpoint}/Data/Documents/wef/   (Office's add-in folder)
# The installer package (SlideMarks.pkg) runs this same script with "--from <folder>".
set -eu

BASE_URL="{{BASE_URL}}"
ADDIN_ID="{{ADDIN_ID}}"
FONT="$HOME/Library/Fonts/SlideMarks-Regular.ttf"
APPS="Word Powerpoint"

wef_dir() { echo "$HOME/Library/Containers/com.microsoft.$1/Data/Documents/wef"; }
app_name() { if [ "$1" = Word ]; then echo Word; else echo PowerPoint; fi; }

uninstall() {
  rm -f "$FONT"
  for app in $APPS; do
    rm -f "$(wef_dir "$app")/$ADDIN_ID".*xml
  done
  echo "SlideMarks removed. Quit and reopen Word and PowerPoint to finish."
}

install() {
  src="${1:-}"
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  if [ -n "$src" ]; then
    cp "$src/SlideMarks-Regular.ttf" "$src/manifest.xml" "$tmp/"
  else
    echo "Downloading SlideMarks from $BASE_URL"
    curl -fsSL "$BASE_URL/download/SlideMarks-Regular.ttf" -o "$tmp/SlideMarks-Regular.ttf"
    curl -fsSL "$BASE_URL/office/manifest.xml" -o "$tmp/manifest.xml"
  fi

  mkdir -p "$(dirname "$FONT")"
  cp "$tmp/SlideMarks-Regular.ttf" "$FONT"
  echo "✓ Font installed"

  blocked=""
  for app in $APPS; do
    container="$HOME/Library/Containers/com.microsoft.$app"
    if [ ! -d "$container" ]; then
      echo "– $(app_name "$app") not found. If it's installed, open it once, then run this again."
      continue
    fi
    # macOS asks "would like to access data from other apps" here; "Don't Allow" makes these fail.
    dir=$(wef_dir "$app")
    if mkdir -p "$dir" && rm -f "$dir/$ADDIN_ID".*xml && cp "$tmp/manifest.xml" "$dir/$ADDIN_ID.SlideMarks.xml"; then
      echo "✓ Add-in added to $(app_name "$app")"
    else
      blocked="$blocked $(app_name "$app")"
    fi
  done

  echo
  if [ -n "$blocked" ]; then
    echo "✗ macOS didn't allow adding the add-in to:$blocked" >&2
    echo "  Run this again and choose Allow when macOS asks to access data from other apps." >&2
    echo "  Help: $BASE_URL/support/#mac-access" >&2
    return 3
  fi
  echo "Next: quit Word and PowerPoint (⌘Q) and reopen them."
  echo "Then click Add-ins on the Home tab, then SlideMarks."
  echo "Help: $BASE_URL/support/#after-install"
}

case "${1:-install}" in
  install) install ;;
  --from) install "$2" ;;
  uninstall) uninstall ;;
  *) echo "usage: install.sh [install | uninstall | --from <folder>]" >&2; exit 2 ;;
esac
