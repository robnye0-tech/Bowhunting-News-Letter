from django.core.management.base import BaseCommand

from newsletter.models import State


class Command(BaseCommand):
    help = (
        "Mark one or more states as launched, making them available on the "
        "public signup form. Run again later with more codes as you build out "
        "content pipelines for additional states — already-launched states are "
        "left alone. To pull a state back off the signup form, toggle its "
        "'Is launched' checkbox in /admin/newsletter/state/ instead."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "codes", nargs="+", help="Two-letter state codes to launch, e.g. ME NH VT NY CT RI NJ PA"
        )

    def handle(self, *args, **options):
        codes = [c.upper() for c in options["codes"]]
        found = State.objects.filter(code__in=codes)
        found_codes = set(found.values_list("code", flat=True))
        missing = [c for c in codes if c not in found_codes]

        already_launched = list(found.filter(is_launched=True).values_list("code", flat=True))
        newly_launched = found.exclude(is_launched=True)
        newly_launched_codes = list(newly_launched.values_list("code", flat=True))
        newly_launched.update(is_launched=True)

        if newly_launched_codes:
            self.stdout.write(self.style.SUCCESS(f"Launched: {', '.join(sorted(newly_launched_codes))}"))
        if already_launched:
            self.stdout.write(f"Already launched (no change): {', '.join(sorted(already_launched))}")
        if missing:
            self.stderr.write(self.style.WARNING(f"Unknown state code(s), skipped: {', '.join(missing)}"))

        total = State.objects.filter(is_launched=True).count()
        self.stdout.write(f"{total} state(s) now launched in total.")
