from django import forms
from django.contrib.auth.models import User
from feed.models import Post, Folder, Comment, UserProfile

class UserForm(forms.ModelForm):
    username = forms.CharField(max_length=36)
    password = forms.CharField(widget=forms.PasswordInput())
    profile_picture = forms.ImageField()
    bio = forms.CharField(max_length=256)
    class Meta:
        model = User
        fields = ('username','password','email','profile_picture')

class UserProfileForm(forms.ModelForm):
    class meta:
        model = UserProfile
        fields = ('website','picture')

class UserLoginForm(forms.ModelForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username' , 'password')

class UserPostsForm(forms.ModelForm):
    title = forms.CharField(max_length=24,required=True)
    image = forms.ImageField()
    
    class Meta:
        model = Post
        fields = ('title','image')

class EditProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=36)
    profile_picture = forms.ImageField()

    class Meta:
        model = User
        fields = {'username','profile_picture' }

class UserCommentForm(forms.ModelForm):
    username = forms.CharField()
    content = forms.CharField(max_length=128)

    class Meta:
        model = Comment
        fields = {'user', 'content'}

class FolderForm(forms.ModelForm):
    foldername = forms.CharField()

    class Meta:
        model = Folder
        fields = {'name'}
