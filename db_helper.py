import time

from model import table


def save_with_retry(items):
    while True:
        if len(items) == 0:
            break
        item = items.pop(0)
        try:
            table.put_item(Item=item)
        except Exception as e:
            print(str(e))
            print('Delaying put of %s' % item.id)
            items.append(item)
            time.sleep(.200)
