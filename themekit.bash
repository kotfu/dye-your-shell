#
# aliases for themekit
#
# Installation:
#   put the following in .bash_profile or .bashrc
#
#   . /path/to/themekit.bash
#

# this should be set when we initialize themekit
if [ -z ${THEMEKIT_DIR+x} ]; then
    THEMEKIT_DIR=~/src/shell-themekit
fi
if [ ! -d $THEMEKIT_DIR ]; then
    echo "Please set THEMEKIT_DIR in ~/.profile to point to the directory of the config repo"
    return
fi
export THEMEKIT_DIR

# these have to be functions instead of scripts so they can add environment
# variables to the "parent" shell

# activate a theme
# theme-activate [FILE | theme_name]
function theme-activate() {

    if [[ -z "$1" ]]; then
        printf "no theme given"
        return 1
    elif [[ -d "$1" ]]; then
        # a directory given on the command line
        export THEME_DIR=$1
    elif [[ -f "$THEMEKIT_DIR/themes/$1/theme.json" ]]; then
        # a theme name, go find it in the themes directory
        export THEME_DIR=$THEMEKIT_DIR/themes/$1
    else
        printf "theme not found"
        return 1
    fi
    theme-reload
}

# reload a theme, setting all theme variables
function theme-reload() {
    for item in $(ls "$THEMEKIT_DIR"/theme.d/*.bash)
    do
        # source these items so they can export environment
        # variables
        source $item
    done
}

theme-activate dracula
