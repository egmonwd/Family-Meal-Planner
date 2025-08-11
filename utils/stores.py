def split_by_store(df):
    buckets = {}
    for store in df['store'].unique():
        buckets[store] = df[df['store'] == store]
    return buckets
