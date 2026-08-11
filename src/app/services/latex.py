"""LaTeX escaping helpers for resume TeX generation."""

_LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(value: str | None) -> str:
    """Escape LaTeX special characters so user content never breaks the file."""
    if value is None:
        return ""
    return "".join(_LATEX_SPECIALS.get(ch, ch) for ch in value)
