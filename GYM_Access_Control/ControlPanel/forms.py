from django import forms

class AppUser_LoginForm(forms.Form):
    email = forms.EmailField(label="E-Posta", widget=forms.EmailInput(attrs={
        'placeholder':'Please enter e-mail address',
        'class':'input100'

    }))

    password = forms.CharField(label="Parola",widget=forms.PasswordInput(attrs={
        'placeholder':'Please enter password',
        'class': 'input100'
    }))