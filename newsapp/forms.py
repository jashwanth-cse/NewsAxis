from django import forms

class ArticleForm(forms.Form):
    name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    mobile = forms.CharField(max_length=10, min_length=10, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'tel', 'pattern': '[0-9]{10}'}))
    title = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}), required=True)
    images = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'multiple': False, 'accept': 'image/jpeg,image/png'}))
    terms = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must accept the Terms and Service.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )