from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post

        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Введите текст',
            'group': 'Выберите группу',
            'image': 'Выберите картинку'
        }
        help_texts = {
            'text': 'Заполнить',
            'group': 'Выбрать группу',
            'image': 'Выбрать картинку'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment

        fields = ('text',)
        labels = {'text': 'Введите текст'}
        help_texts = {'text': 'Заполнить'}
