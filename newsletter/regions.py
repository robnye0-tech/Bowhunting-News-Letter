from .models import State

# Grouping for the signup form only (display/navigation aid) — not stored on
# the State model since it doesn't affect content, subscriptions, or sends.
REGION_MAP = {
    "Northeast": ["CT", "ME", "MA", "NH", "NJ", "NY", "PA", "RI", "VT"],
    "Midwest": ["IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "ND", "OH", "SD", "WI"],
    "South": [
        "AL", "AR", "DE", "FL", "GA", "KY", "LA", "MD", "MS",
        "NC", "OK", "SC", "TN", "TX", "VA", "WV", "DC",
    ],
    "West": ["AZ", "CA", "CO", "ID", "MT", "NV", "NM", "OR", "UT", "WA", "WY"],
    "Alaska & Hawaii": ["AK", "HI"],
}


def grouped_states():
    """Return [(region_label, [State, ...]), ...] using REGION_MAP order,
    with states in each group ordered by name. Only includes launched states
    — the ones actually offered on the public signup form."""
    states_by_code = {s.code: s for s in State.objects.filter(is_launched=True)}
    groups = []
    for label, codes in REGION_MAP.items():
        states = sorted(
            (states_by_code[code] for code in codes if code in states_by_code),
            key=lambda s: s.name,
        )
        if states:
            groups.append((label, states))
    return groups
