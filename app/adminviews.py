from urllib.parse import urlencode
from app.sections import SectionRows
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
        dbsis_url = 'https://dbsis.herokuapp.com'

        connection = mail.get_connection()
        connection.open()
        msgs = []
        sections = Section.objects.all()

        for parent in parents:
            user = parent.users.first()
            signup_url = dbsis_url + '/app/login?' + urlencode({
                'name':         parent.name,
                'email':        parent.email,
                'parent_code':  parent.code
            }) if parent.code and not user else None

            rows = SectionRows(sections, user)
            html_content = status_template.render({
                'parent':       parent,
                'dbsis_url':    dbsis_url,
                'signup_url':   signup_url,
                'section_rows': rows,
                'show_students': True,
            })
            text_content = html2text.html2text(html_content)

            msg = EmailMultiAlternatives('Status of Dave B’s Young Programmers', text_content,
                'Dave B’s Student Information System <daveb@davebsoft.com>', ['%s <%s>' % (parent.name, parent.email)])
            msg.attach_alternative(html_content, "text/html")
            msgs.append(msg)

        connection.send_messages(msgs)
        connection.close()

        return redirect(reverse('admin'))
