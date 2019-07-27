from pynamodb.attributes import (
    UnicodeAttribute)
from pynamodb.models import Model


class EventWrapper(Model):

    class Meta:
        table_name = 'aws-scheduler-events'

    id = UnicodeAttribute(hash_key=True)
    date = UnicodeAttribute()
    payload = UnicodeAttribute()
    target = UnicodeAttribute()
    status = UnicodeAttribute(default='NEW')
    user = UnicodeAttribute(null=True)
