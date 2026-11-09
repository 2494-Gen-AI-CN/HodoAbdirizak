import pandas as pd
from cleansing import add_typed_columns, split_good_and_rejects

df = pd.read_csv("data/ems_incidents.csv", dtype=str)
df = add_typed_columns(df)

good, rejects = split_good_and_rejects(df)

print("Total:", len(df), " Good:", len(good), " Rejected:", len(rejects))
print(rejects["reject_reason"].value_counts())
print("Check:", len(good) + len(rejects) == len(df))