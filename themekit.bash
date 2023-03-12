#
# aliases for themekit
#
# Installation:
#   put the following in .bash_profile or .bashrc
#
#   . /path/to/themekit.bash
#

# this should be set when we initialize themekit
# you can of course override this environment variable at any time
if [[ -z "$THEMEKIT_DIR" ]]; then
    export THEMEKIT_DIR=~/src/shell-themekit
fi

# these have to be functions instead of scripts so they can add environment
# variables to the "parent" shell

# activate a theme
# theme-activate [FILE | theme_name]
function theme-activate() {

    if [[ -z "$1" ]]; then
        printf "no theme given"
        return 1
    elif [[ -f "$1" ]]; then
        export THEME_FILE=$1
    elif [[ -f "$THEMEKIT_DIR/themes/$1/theme.json" ]]; then
        export THEME_FILE=$THEMEKIT_DIR/themes/$1/theme.json
    else
        printf "theme not found"
        return 1
    fi
    theme-reload
}

# reload a theme, setting all theme variables
function theme-reload() {
    for item in $(ls $THEMEKIT_DIR/theme.d)
    do
        # source these items so they can export environment
        # variables
        . $THEMEKIT_DIR/theme.d/$item
    done
}

theme-activate dracula
