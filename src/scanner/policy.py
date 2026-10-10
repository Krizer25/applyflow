import ipaddress


def _valid_hostname(value):
    if not value or len(value) > 253:
        return False

    labels = value.split(".")

    for label in labels:
        if not label or len(label) > 63:
            return False

        if label.startswith("-") or label.endswith("-"):
            return False

        if not all(
            character.isascii()
            and (character.isalnum() or character == "-")
            for character in label
        ):
            return False

    return True


def normalize_target(value):
    value = value.strip().lower().rstrip(".")

    if not value:
        raise ValueError("Target cannot be empty.")

    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        pass

    if not _valid_hostname(value):
        raise ValueError(
            "Use an exact hostname or IP address. "
            "URLs, wildcards, ranges and commands are rejected."
        )

    return value


def require_scope(target, allowed_targets):
    target = normalize_target(target)

    if target not in allowed_targets:
        raise ValueError(f"Target is outside recorded scope: {target}")

    return target
