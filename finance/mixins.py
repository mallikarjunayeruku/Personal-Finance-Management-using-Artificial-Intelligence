from __future__ import annotations


class OwnedQuerysetMixin:
    owner_field = "user"           # set to "owner" if your other models use that
    default_ordering: tuple[str, ...] | None = None

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_authenticated:
            qs = qs.filter(**{self.owner_field: self.request.user})
        if self.default_ordering and not qs.query.order_by:
            qs = qs.order_by(*self.default_ordering)
        return qs
