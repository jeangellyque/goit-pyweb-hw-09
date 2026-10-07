from mongoengine import (
    BooleanField,
    Document,
    EmailField,
    ListField,
    ReferenceField,
    StringField,
)


class Author(Document):
    fullname = StringField(required=True, unique=True)
    born_date = StringField(required=True)
    born_location = StringField(required=True)
    description = StringField(required=True)

    meta = {"collection": "authors"}


class Quote(Document):
    tags = ListField(StringField(), required=True)
    author = ReferenceField(Author, required=True)
    quote = StringField(required=True)

    meta = {"collection": "quotes"}


class Contact(Document):
    fullname = StringField(required=True)
    email = EmailField(required=True, unique=True)
    phone_number = StringField(required=True)
    preferred_channel = StringField(
        required=True,
        choices=("email", "sms"),
        default="email",
    )
    email_sent = BooleanField(required=True, default=False)
    sms_sent = BooleanField(required=True, default=False)

    meta = {"collection": "contacts"}
