from datetime import datetime
from urllib.parse import urlencode
from django.core import mail
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.generic import View
from django.core.mail import EmailMultiAlternatives
import html2text
from app.models import Parent, Section


class Admin(View):
    def get(self, request):
        return render(request, 'app/admin.html')


class AdminEmail(View):
    def get(self, request):
        status_template = get_template('app/email/status.html')
        parents = Parent.objects.exclude(email__isnull=True).exclude(email__exact='')
        sections = Section.objects.filter(start_time__gt=datetime.now()).order_by('start_time')
        dbsis_url = 'https://dbsis.herokuapp.com'

        connection = mail.get_connection()
        connection.open()
        msgs = []

        for parent in parents:
            users = parent.users.all()
            signup_url = dbsis_url + '/app/login?' + urlencode({
                'name':         parent.name,
                'email':        parent.email,
                'parent_code':  parent.code
            }) if parent.code and not users else None

            html_content = status_template.render({
                'parent':       parent,
                'dbsis_url':    dbsis_url,
                'signup_url':   signup_url,
                'sections':     sections,
            })
            text_content = html2text.html2text(html_content)

            msg = EmailMultiAlternatives('Status of Dave B’s Young Programmers', text_content,
                'Dave B’s Student Information System <daveb@davebsoft.com>', ['%s <%s>' % (parent.name, parent.email)])
            msg.attach_alternative(html_content, "text/html")
            msgs.append(msg)

        connection.send_messages(msgs)
        connection.close()

        return redirect(reverse('admin'))