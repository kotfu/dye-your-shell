#
# fzf configuration
#
# gotta run this like ". fdirs" or it won't work

# get the elements and their colors
lines=$($THEMEKIT_DIR/bin/themeparser fzf)

# see the done part of this loop for the input
# we use this method so we don't create a subshell
# this way the variables that we set will persist in our
# parent shell

# unset THEME_FDIRS_PROMPT
# unset THEME_FDIRS_MATCH
# unset THEME_FDIRS_TEXT
# unset THEME_FDITS_INDICATOR

fzfcoloropts = ()
while IFS= read -r line; do
    scope=$(expr "$line" : '\(.*\):')
    color=$(expr "$line" : '.*:\(.*\)')
    case "$scope" in
        fzf.text)
            fzfcoloropts+=("fg:regular:$color")
            ;;
        fzf.label)
            fzfcoloropts+=("label:$color")
            ;;
        fzf.border)
            fzfcoloropts+=("border:$color")
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




function __control_r_fzf_opts() {
    local FZFOPTS=("--pointer=•" "--info=hidden" "-i" "--no-sort")
    # "--height=~40%"
#    FZFOPTS+=("--layout=reverse")
    FZFOPTS+=("--border" "--border-label='command history'" "--border-label-pos=3")
    # set colors
    FZFOPTS+=("--color=fg:regular:$THEME_FDIRS_TEXT,label:$THEME_FDIRS_LABEL")
    # the border
    FZFOPTS+=("--color=border:$THEME_FDIRS_BORDER")
    # fg+ and bg+ are colors for the currently selected line
    FZFOPTS+=("--color=fg+:regular,bg+:regular:$THEME_FDIRS_SELECTED,gutter:-1")
    # the indicator pointing to the selected item, and the prompt in front of the
    # characters yous type
    FZFOPTS+=("--color=pointer:$THEME_FDIRS_INDICATOR,prompt:$THEME_FDIRS_PROMPT")
    # these are the characters you type
    FZFOPTS+=("--color=query:regular:$THEME_FDIRS_MATCH")
    # hl is the highlighted characters that match the search
    FZFOPTS+=("--color=hl:regular:$THEME_FDIRS_MATCH,hl+:regular:$THEME_FDIRS_MATCH")
    FZFOPTS+=("--bind=ctrl-k:kill-line,ctrl-j:ignore,ctrl-u:unix-line-discard")
    echo ${FZFOPTS[@]}
}
export FZF_CTRL_R_OPTS="$(__control_r_fzf_opts)"