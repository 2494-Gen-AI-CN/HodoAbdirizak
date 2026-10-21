import numpy as np
import pandas as pd

numbers = np.array([10, 20, 30, 40])
print("NumPy mean:", numbers.mean())

students = pd.DataFrame(
    {
        "name": ["Alice", "Bob"],
        "score": [88, 92],
    }
)

print("\nPandas table:")
print(students)
print("\nAverage score:", students["score"].mean())
