import pandas as pd
from cleansing import add_typed_columns, split_good_and_rejects

df = pd.read_csv("data/EMS_Incident_Dispatch_Data_20261104.csv", nrows=1000, dtype=str)
df = add_typed_columns(df)

good, rejects = split_good_and_rejects(df)

print("Total:", len(df), " Good:", len(good), " Rejected:", len(rejects))
print(rejects["reject_reason"].value_counts())
print("Check:", len(good) + len(rejects) == len(df))