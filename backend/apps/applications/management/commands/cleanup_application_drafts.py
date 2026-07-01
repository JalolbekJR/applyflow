from django.core.management.base import BaseCommand, CommandError

from apps.applications.cleanup import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_ORPHAN_GRACE_HOURS,
    MAX_BATCH_SIZE,
    cleanup_application_drafts,
)


class Command(BaseCommand):
    help = "Clean expired application drafts and private draft document storage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply cleanup mutations. Omit for a dry-run.",
        )
        parser.add_argument(
            "--batch-size",
            default=DEFAULT_BATCH_SIZE,
            help=f"Maximum records or objects per cleanup stage. Max: {MAX_BATCH_SIZE}.",
        )
        parser.add_argument(
            "--orphan-grace-hours",
            default=DEFAULT_ORPHAN_GRACE_HOURS,
            help="Minimum age for unreferenced private draft objects.",
        )

    def handle(self, *args, **options):
        batch_size = positive_int_option(
            options["batch_size"],
            name="batch-size",
            maximum=MAX_BATCH_SIZE,
        )
        orphan_grace_hours = positive_int_option(
            options["orphan_grace_hours"],
            name="orphan-grace-hours",
            maximum=24 * 365,
        )
        summary = cleanup_application_drafts(
            apply=options["apply"],
            batch_size=batch_size,
            orphan_grace_hours=orphan_grace_hours,
        )
        for line in summary.lines():
            self.stdout.write(line)
        if summary.total_failures:
            raise CommandError("Cleanup completed with item failures.")


def positive_int_option(value, *, name: str, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise CommandError(f"{name} must be a positive integer.") from exc
    if str(value).strip() != str(parsed):
        raise CommandError(f"{name} must be a positive integer.")
    if parsed <= 0:
        raise CommandError(f"{name} must be a positive integer.")
    if parsed > maximum:
        raise CommandError(f"{name} must be no greater than {maximum}.")
    return parsed
