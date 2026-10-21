# Week 2: NumPy and Pandas Demo

This project loads the airport traffic dataset from Kaggle and shows a simple Pandas workflow.

## Setup

```bash
cd week-2-numpy-pandas-demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Kaggle setup

This script tries to download the dataset from:
https://www.kaggle.com/datasets/nilesh2042/airport-traffic-dataset/data

You need a Kaggle account and Kaggle API credentials configured in ~/.kaggle/kaggle.json.

If you already have the CSV locally, you can set:

```bash
export AIRPORT_DATA_PATH="/path/to/your/airport_traffic.csv"
python demo.py
```

## Run

```bash
python demo.py
```


