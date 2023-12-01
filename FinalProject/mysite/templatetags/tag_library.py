from django import template

register = template.Library()


@register.filter()
def to_float(value):
    return float(value)


@register.filter(name='zip')
def zip_lists(a, b):
    return zip(a, b)
