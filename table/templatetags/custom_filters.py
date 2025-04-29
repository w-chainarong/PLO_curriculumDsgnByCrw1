from django import template

register = template.Library()

@register.filter
def index(sequence, position):
    try:
        position = int(position)
        return sequence[position - 1]
    except (IndexError, ValueError, TypeError):
        return ''

@register.filter
def split(value, delimiter=","):
    return value.split(delimiter)

@register.filter(name='to_range')
def to_range(value):
    try:
        value = int(value)
        return range(1, value + 1)
    except (ValueError, TypeError):
        return range(0)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)

@register.filter(name='sum_list')
def sum_list(value):
    try:
        return sum(value)
    except TypeError:
        return 0

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def map(value, attr_name):
    try:
        return [getattr(obj, attr_name, 0) for obj in value]
    except:
        return []