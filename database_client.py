import time
from random import random

from model import table


def put_items(items):
    print('Saving %d items' % len(items))
    while True:
        if len(items) == 0:
            break
        item = items.pop(0)
        try:
            table.put_item(Item=item)
        except Exception as e:
            if 'ThrottlingException' in str(e):
                print('Delaying put of %s' % item.id)
                items.append(item)
                time.sleep(.100 + random() / 4.0)
            else:
                print(str(e))
                raise e
