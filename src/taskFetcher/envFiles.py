import os
import shlex
import stat


def permission_warnings(paths) -> list[str]:
    """A warning for each existing file that its group or other users can read.

    Names the path and mode, never the contents. Skipped where there are no POSIX modes.
    """
    if os.name != "posix":
        return []
    warnings = []
    for path in paths:
        if not path:
            continue
        try:
            mode = stat.S_IMODE(os.stat(path).st_mode)
        except OSError:
            continue
        if mode & (stat.S_IRGRP | stat.S_IROTH):
            warnings.append(f"Warning: {path} is mode {mode:03o} and can be read by others; "
                            f"run: chmod 600 {shlex.quote(str(path))}")
    return warnings
