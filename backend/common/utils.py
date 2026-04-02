from django.utils.text import slugify


def build_unique_slug(model_class, value: str, instance=None, slug_field: str = "slug") -> str:
    base_slug = slugify(value)[:220] or "item"
    slug = base_slug
    counter = 1

    queryset = model_class.objects.all()
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    while queryset.filter(**{slug_field: slug}).exists():
        suffix = f"-{counter}"
        slug = f"{base_slug[: 255 - len(suffix)]}{suffix}"
        counter += 1

    return slug

