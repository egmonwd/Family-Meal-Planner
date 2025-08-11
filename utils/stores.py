def split_by_store(df):
    buckets={}
    for s in df['store'].unique():
        buckets[s]=df[df['store']==s]
    return buckets
