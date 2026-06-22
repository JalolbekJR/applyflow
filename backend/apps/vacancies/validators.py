from django.core.exceptions import ValidationError


def validate_string_list(value: object) -> None:
    if not isinstance(value, list) or len(value) > 20:
        raise ValidationError("Enter a list containing no more than 20 items.")
    if any(not isinstance(item, str) or not item.strip() or len(item) > 120 for item in value):
        raise ValidationError("Each list item must be non-empty text under 120 characters.")
