#
# gotta run this like ". fdirs" or it won't work

# get the elements and their colors
lines=$($THEMEKIT_DIR/bin/themeparser fdirs)

# see the done part of this loop for the input
# we use this method so we don't create a subshell
# this way the variables that we set will persist in our
# parent shell

unset THEME_FDIRS_PROMPT
unset THEME_FDIRS_MATCH
unset THEME_FDIRS_TEXT
unset THEME_FDITS_INDICATOR

while IFS= read -r line; do
    scope=$(expr "$line" : '\(.*\):')
    color=$(expr "$line" : '.*:\(.*\)')
    case "$scope" in
        fdirs.label)
            export THEME_FDIRS_LABEL=$color
            ;;
        fdirs.border)
            export THEME_FDIRS_BORDER=$color
            ;;
        fdirs.text)
            export THEME_FDIRS_TEXT=$color
            ;;
        fdirs.prompt)
            export THEME_FDIRS_PROMPT=$color
            ;;        
        fdirs.match)
            export THEME_FDIRS_MATCH=$color
            ;;
        fdirs.indicator)
            export THEME_FDIRS_INDICATOR=$color
            ;;
        fdirs.selected)
            export THEME_FDIRS_SELECTED=$color
            ;;
    esac
done <<< "$lines"
