"""Function to generate filter queryset"""


def custom_filter(model, filter_items):
    return model.objects.filter(**filter_items)
