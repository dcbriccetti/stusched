from django.template import Library
from django.urls import resolve

register = Library()


@register.simple_tag
def active_nav(request, url):
    return 'active' if resolve(request.path).url_name == url else ''
