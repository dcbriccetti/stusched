from django.core.urlresolvers import resolve
from django.template import Library

register = Library()


@register.simple_tag
def active_nav(request, url):
    return 'active' if resolve(request.path).url_name == url else ''
