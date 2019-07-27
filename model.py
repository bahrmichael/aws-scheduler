import os

from pynamodb.attributes import (
    UnicodeAttribute)
from pynamodb.models import Model

stage = os.environ.get('STAGE')


class EventWrapper(Model):

    class Meta:
        table_name = f'aws-scheduler-events-{stage}'

    id = UnicodeAttribute(hash_key=True)
    date = UnicodeAttribute()
    payload = UnicodeAttribute()
    target = UnicodeAttribute()
    status = UnicodeAttribute(default='NEW')
    user = UnicodeAttribute(null=True)
