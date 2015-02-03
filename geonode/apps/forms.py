from django import forms
from django.core.validators import validate_email, ValidationError
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth import get_user_model

from geonode.apps.models import App, AppCategory


class AppForm(forms.ModelForm):

    slug = forms.SlugField(
        max_length=20,
        help_text=_("a short version of the name consisting only of letters, numbers, underscores and hyphens."),
        widget=forms.HiddenInput,
        required=False)

    email = forms.URLField(
        label='URL'
        )

    is_service = forms.BooleanField(
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):

        if 'is_service' in kwargs:
            is_service = kwargs.pop('is_service') 
        elif 'instance' in kwargs:
            is_service = kwargs['instance'].is_service
        else:
            is_service = False
            
        kwargs['initial'] = kwargs.get('initial',{})
        kwargs['initial']['is_service'] = is_service
        super(AppForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = AppCategory.objects.filter(is_service=is_service)
        if is_service:
            del self.fields['email']
            del self.fields['widget_url']

    def clean_slug(self):
        if App.objects.filter(
                slug__iexact=self.cleaned_data["slug"]).count() > 0:
            raise forms.ValidationError(
                _("A group already exists with that slug."))
        return self.cleaned_data["slug"].lower()

    def clean_title(self):
        if App.objects.filter(
                title__iexact=self.cleaned_data["title"]).count() > 0:
            raise forms.ValidationError(
                _("A group already exists with that name."))
        return self.cleaned_data["title"]

    def clean(self):
        cleaned_data = self.cleaned_data

        name = cleaned_data.get("title")
        slug = slugify(name)

        cleaned_data["slug"] = slug

        return cleaned_data

    class Meta:
        model = App
        # exclude = ['group']




class AppUpdateForm(forms.ModelForm):

    def clean_name(self):
        if App.objects.filter(
                name__iexact=self.cleaned_data["title"]).count() > 0:
            if self.cleaned_data["title"] == self.instance.name:
                pass  # same instance
            else:
                raise forms.ValidationError(
                    _("A group already exists with that name."))
        return self.cleaned_data["title"]

    class Meta:
        model = App
        # exclude = ['group']


# class GroupMemberForm(forms.Form):
#     role = forms.ChoiceField(choices=[
#         ("member", "Member"),
#         ("manager", "Manager"),
#     ])
#     user_identifiers = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 'class': 'user-select'}))

#     def clean_user_identifiers(self):
#         value = self.cleaned_data["user_identifiers"]
#         new_members, errors = [], []

#         for ui in value.split(","):
#             ui = ui.strip()

#             try:
#                 validate_email(ui)
#                 try:
#                     new_members.append(get_user_model().objects.get(email=ui))
#                 except get_user_model().DoesNotExist:
#                     new_members.append(ui)
#             except ValidationError:
#                 try:
#                     new_members.append(
#                         get_user_model().objects.get(
#                             username=ui))
#                 except get_user_model().DoesNotExist:
#                     errors.append(ui)

#         if errors:
#             message = (
#                 "The following are not valid email addresses or "
#                 "usernames: %s; not added to the group" %
#                 ", ".join(errors))
#             raise forms.ValidationError(message)

#         return new_members


# class GroupInviteForm(forms.Form):

#     invite_role = forms.ChoiceField(label="Role", choices=[
#         ("member", "Member"),
#         ("manager", "Manager"),
#     ])
#     invite_user_identifiers = forms.CharField(
#         label="E-mail addresses list",
#         widget=forms.Textarea)

#     def clean_user_identifiers(self):
#         value = self.cleaned_data["invite_user_identifiers"]
#         invitees, errors = [], []

#         for ui in value.split(","):
#             ui = ui.strip()

#             try:
#                 validate_email(ui)
#                 try:
#                     invitees.append(get_user_model().objects.get(email=ui))
#                 except get_user_model().DoesNotExist:
#                     invitees.append(ui)
#             except ValidationError:
#                 try:
#                     invitees.append(get_user_model().objects.get(username=ui))
#                 except get_user_model().DoesNotExist:
#                     errors.append(ui)

#         if errors:
#             message = (
#                 "The following are not valid email addresses or "
#                 "usernames: %s; no invitations sent" %
#                 ", ".join(errors))
#             raise forms.ValidationError(message)

#         return invitees
