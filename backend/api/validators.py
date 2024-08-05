from django.core.validators import RegexValidator

username_validator = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message='Недопустимые символы в имени',
    code='invalid_username',
)

tag_validator = RegexValidator(
    regex=r'^[-a-zA-Z0-9_]+$',
    message='Некорректное имя слага',
    code='invalid_tag',
)
