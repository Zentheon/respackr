# respackr/ascii.py


from respackr import __version__

"""Mappings of logo ascii art and other fun little things"""

MINECART = r"""
_|▔▔▔▔▔▔▔|
"└─▬───▬─┘
"""

CHEST_MINECART = r"""
_________
│ %ver%
│ ┌─────┐
│ ┝━━■━━┥
┴|▔▔▔▔▔▔▔|
"└─▬───▬─┘
"""

LOGO_LETTERS = {
    "r": r"""
▗▄▄▖
▐▌ ▐▌
▐▛▀▚▖
▐▌ ▐▌
""",
    "e": r"""
▗▄▄▄▖
▐▌
▐▛▀▀▘
▐▙▄▄▖
""",
    "s": r"""
 ▗▄▄▖
▐▌
 ▝▀▚▖
▗▄▄▞▘
""",
    "p": r"""
▗▄▄▖
▐▌ ▐▌
▐▛▀▘
▐▌
""",
    "a": r"""
 ▗▄▖
▐▌ ▐▌
▐▛▀▜▌
▐▌ ▐▌
""",
    "c": r"""
 ▗▄▄▖
▐▌
▐▌
▝▚▄▄▖
""",
    "k": r"""
▗▖ ▗▖
▐▌▗▞▘
▐▛▚▖
▐▌ ▐▌
""",
}

CAVE = r"""
█████▄▄
█████████
█████▀
█████⛏
█████
████████████
"""

VERSION_SYMBOLS = {
    0: "▄▖\n▛▌\n█▌",
    1: "▗ \n▜ \n▟▖",
    2: "▄▖\n▄▌\n▙▖",
    3: "▄▖\n▄▌\n▄▌",
    4: "▖▖\n▙▌\n ▌",
    5: "▄▖\n▙▖\n▄▌",
    6: "▄▖\n▙▖\n▙▌",
    7: "▄▖\n▌ \n▌ ",
    8: "▄▖\n▙▌\n▙▌",
    9: "▄▖\n▙▌\n▄▌",
    ".": "  \n  \n▗ ",
}


def assemble_logo(input_str="respackr") -> list:
    """Constructs a list of lines of an ascii artified string

    Takes a dict of ascii art letters mapped to their respective character and appends them
    to a list of lines based on an input string. It aligns the letters based on a decorative
    lower part, and also adds a final fixed "character" to the end that's just any string.
    """
    set_width = 10  # The fixed width of each character
    lpadding = 3  # How much to pad letters to align with decoration
    letter_height = 4  # Height of letter art characters

    logo_rows = []

    # Loop through each character in the __name__ variable
    for char in input_str:
        if char in LOGO_LETTERS:
            # Get the letter corresponding to the character and add its lines to logo_rows
            ascii_art = LOGO_LETTERS[char]
            # Add the "minecart" to each letter
            ascii_art += "\n" + MINECART

            lines = [line for line in ascii_art.split("\n") if line.strip()]
            for i, line in enumerate(lines):
                while len(logo_rows) <= i:  # Ensure we have enough strings in logo_rows
                    logo_rows.append("")

                # Pad the line with whitespace to make it the correct length
                if i < letter_height:
                    line = " " * lpadding + line  # leftside align letters
                padded_line = line.ljust(set_width)
                logo_rows[i] += padded_line

    # Append chest minecart
    lines = [line for line in CHEST_MINECART.split("\n") if line.strip()]
    for i, line in enumerate(lines):
        if "%ver%" in line:
            line = line.replace("%ver%", "v" + __version__)
        logo_rows[i] += line

    return logo_rows
