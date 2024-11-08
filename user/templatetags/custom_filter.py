from django import template

register = template.Library()

@register.filter
def isnumeric(value):
    return str(value).isnumeric()
