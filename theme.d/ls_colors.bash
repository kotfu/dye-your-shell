#
# gotta run this like ". ls_colors" or it won't work

# set the ls colors from the theme
if [[ -f "$THEME_DIR/ls_colors.bash" ]]; then
    source "$THEME_DIR/ls_colors.bash"
fi
