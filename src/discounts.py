def apply_discount(percent, code, expired=False):
    """Apply a percent discount. Caps and expiry are not enforced yet."""
    return {"ok": True, "percent": percent, "code": code}