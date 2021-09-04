
# Locust load tests

[Locust](https://locust.io/) is a Python utility for doing easy, distributed
load testing of a web site.

## Prerequisites

* Python 3.6+

Install the the required Python packages

```
pip install -r requirements.txt
```

## Usage

Web-UI: execute
```

locust -f load_test.py --host=http://localhost:9000
```
and open `http://localhost:8089/` in a web browser.

Non-interactive tests:
```
locust --headless -u 300 -r 2 --only-summary -f load_test.py --host http://localhost:9000
```
