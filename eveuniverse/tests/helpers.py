from django.db.models import QuerySet


def queryset_pks(queryset: QuerySet) -> set:
    """shortcut that returns the pks of the given queryset as set.
    Useful for comparing test results.
    """
    return set(queryset.values_list("pk", flat=True))
