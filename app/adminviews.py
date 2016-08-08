from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.generic import View
from django.core.mail import EmailMultiAlternatives
import html2text


class Admin(View):
    def get(self, request):
        return render(request, 'app/admin.html')


class AdminEmail(View):
    def get(self, request):
        class ESection:
            def __init__(self, time, title):
                self.time = time
                self.title = title

        t = get_template('app/email/upcoming.html')
        html_content = t.render({'sections': (ESection('Monday', '3D Animation with Processing'),)})
        text_content = html2text.html2text(html_content)
        msg = EmailMultiAlternatives('Upcoming classes', text_content,
            'Dave B’s Student Information System <daveb@davebsoft.com>', ['daveb@davebsoft.com'])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return redirect(reverse('admin'))
