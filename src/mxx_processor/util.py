


def chunk_list(lst, chunk_size=16):
    return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]

