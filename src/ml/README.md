# ML Module

## Setup

```bash
python3 -m venv pyenv-sendsmart-ml
source pyenv-sendsmart-ml/bin/activate
pip install -r requirements.txt
```

## Usage

### 1. Fetch historical FX data

```bash
python3 data/fetch_historical.py
```

### 2. Train the global timing model

```bash
python3 train.py
```

### 3. Run tests

```bash
python3 test/test_main.py
```