from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
from .models import Student, Parent


class AuthenticationForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    username = forms.CharField(max_length=254)
    password = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': _("Please enter a correct %(username)s and password. "
                           "Note that both fields may be case-sensitive."),
        'inactive': _("This account is inactive."),
    }

    def __init__(self, *args, **kwargs):
        """
        The form data comes in via the standard 'data' kwarg.
        """
        self.user_cache = None
        super(AuthenticationForm, self).__init__(*args, **kwargs)

        # Set the label for the "username" field.
        UserModel = get_user_model()
        self.username_field = UserModel._meta.get_field(UserModel.USERNAME_FIELD)
        if self.fields['username'].label is None:
            self.fields['username'].label = capfirst(self.username_field.verbose_name)
        # todo: Set autofocus on the username field in the top form unless we got here via a link with a parent code

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class NewUserForm(forms.Form):
    name        = forms.CharField(max_length=100, help_text='The full name of a parent or parents')
    username    = forms.CharField(min_length=1, max_length=254)
    password    = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput)
    email       = forms.EmailField(label='Email address')
    parent_code = forms.CharField(required=False, max_length=100,
        help_text='A code, if one was provided to you, to tie this new account to an existing parent record.')

    error_messages = {
        'invalid_code': _(""),
    }

    def clean_parent_code(self):
        code = self.cleaned_data.get('parent_code')
        if code and not Parent.objects.filter(code=code).first():
            raise forms.ValidationError(
                'Unrecognized code. Please enter the code you were given, or leave the field blank.')
        return code

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).first():
            raise forms.ValidationError('That username already exists.', code=USER_EXISTS_ERROR_CODE)
        return username

USER_EXISTS_ERROR_CODE = 'user-exists'


class ParentForm(ModelForm):
    class Meta:
        model = Parent
        fields = ('name', 'phone', 'email', 'referred_by')

    def __init__(self, *args, **kwargs):
        super(ParentForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True


class StudentForm(ModelForm):
    class Meta:
        model = Student
        fields = ('name', 'birthdate', 'grade_from_age', 'school', 'email', 'when_available', 'notes')

    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        for name in ('birthdate', 'grade_from_age'):
            self.fields[name].required = True
