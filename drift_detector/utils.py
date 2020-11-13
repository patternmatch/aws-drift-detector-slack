def chunks(collection, single_chunk_size):
    for i in range(0, len(collection), single_chunk_size):
        yield collection[i:i + single_chunk_size]
