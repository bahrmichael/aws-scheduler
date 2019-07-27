import time

from pynamodb.exceptions import PutError, DeleteError


def save_with_retry(items):
    while True:
        if len(items) == 0:
            break
        item = items.pop(0)
        try:
            item.save()
        except PutError as e:
            print(e)
            print('Delaying put of %s' % item.id)
            items.append(item)
            time.sleep(.200)


def delete_with_retry(items):
    while True:
        if len(items) == 0:
            break
        item = items.pop(0)
        try:
            item.delete()
        except DeleteError as e:
            print(e)
            print('Delaying deletion of %s' % item.id)
            items.append(item)
            time.sleep(.200)
