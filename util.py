
def make_chunks(l, chunk_length):
    # Yield successive n-sized chunks from l.
    for i in range(0, len(l), chunk_length):
        yield l[i:i + chunk_length]
