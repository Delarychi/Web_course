from django import template
from session_controller.models import Session

register = template.Library()

@register.inclusion_tag('sessions_list.html')
def show_sessions():
    sessions = Session.objects.filter(is_active=True)
    return {'sessions': sessions}
