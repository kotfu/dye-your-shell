# shell themes

- create a json based file format that contains element names and style
- maybe check out the .tmTheme format, it's popular, but it's complex, we could just use scopes we like
- see tmtheme-to-json for a way to turn the theme file into json
- use jq to parse and manage theme files
- have a dotfile that contains the theme to use, have a gum powered  command to select from the themes
- make a shell script or program that can parse the theme file and create dircolors, and set gum environment variables, prompt stuff, man pager and whatever else, to make the colors from the theme effective
- look at the dracula theme for a color palette and theme specification to get started with

- Create documentation for the theme scopes and what we turn them into.
- see how gum specifies colors


Extracting a style from a scope:
```
$ jq '.ls.directory' example.json
```


- need a way to resolve a scope to a {hexcolor, escape sequence}
- add gum to the theme and set gum environment variables as a catch all

- apply a theme
	- make a plugin for each shell program we are going to apply the theme to
	- the plugin gets the resolved scopes for the theme
