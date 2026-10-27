class TaskSource:
    """Where the display's tasks come from: fetching them, wording its errors, and its screen layout."""
    name = ""
    two_columns = False

    def fetch(self):
        raise NotImplementedError

    def describe_error(self, error: Exception) -> tuple[str, str]:
        """Heading and detail for the on-screen notice. Never includes the error text, which may hold secrets."""
        raise NotImplementedError

    def __repr__(self):
        # Name only: a source holds credentials and ids, and a repr ends up in logs and tracebacks.
        return f"<{self.name} source>"


def http_status(error: Exception):
    return getattr(getattr(error, "response", None), "status_code", None)
