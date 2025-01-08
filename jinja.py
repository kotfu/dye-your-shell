#
#
import jinja2
import rich.style


def fg_hex(value):
    if value.color:
        return value.color.get_truecolor().hex
    return value


def fg_hexnohash(value):
    if value.color:
        return value.color.get_truecolor().hex.replace("#", "")
    return value


def fg_rgb(value):
    if value.color:
        return value.color.get_truecolor().rgb
    return value


def bg_hex(value):
    if value.bgcolor:
        return value.bgcolor.get_truecolor().hex
    return value


def bg_rgb(value):
    if value.color:
        return value.bgcolor.get_truecolor().rgb
    return value


def ansi_on(value):
    splitter = "-----"
    ansistring = value.render(splitter)
    out, _ = ansistring.split(splitter)
    return out


def ansi_off(value):
    splitter = "-----"
    ansistring = value.render(splitter)
    _, out = ansistring.split(splitter)
    return out


env = jinja2.Environment()
env.filters["fg_hex"] = fg_hex
env.filters["fg_rgb"] = fg_rgb
env.filters["bg_hex"] = bg_hex
env.filters["bg_rgb"] = bg_rgb
env.filters["fg_hex_nohash"] = fg_hexnohash
env.filters["ansi_on"] = ansi_on
env.filters["ansi_off"] = ansi_off
#
gbls = {}
gbls["greeting"] = "Hello there."
gbls["response"] = "General Kenobi."
styles = {}
styles["qqq"] = rich.style.Style.parse("#ff0000 on white")
styles["blue"] = rich.style.Style.parse("bold bright_white on blue1")
gbls["style"] = styles
env.globals = gbls


# template = env.get_template("filename.html")
template = env.from_string(
    "({{style.qqq}}) fg_hex={{ style.qqq|fg_hex }} fg_rgb={{style.qqq|fg_rgb}} bg_hex={{style.qqq|bg_hex}} bg_rgb={{style.qqq|bg_rgb}} fg_hex_nohash={{style.qqq|fg_hex_nohash}}"
)
print(template.render())

template = env.from_string("{{style.blue|ansi_on}}Hello there.{{style.blue|ansi_off}}")
print(template.render())
