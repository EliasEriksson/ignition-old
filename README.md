# ignition

Rewrite of codescord to a webbservice.

Written in python3.9.

## Non python Dependencies

* Docker

## Install and run

If your user does not have access to docker commands 
`python` must be replaced with `venv/bin/python` in the commands using `main.py`.

0. `git clone https://github.com/eliaseriksson/ignition && cd ignition`
1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `python -m pip install -r requirements.txt`
4. `python main.py build-docker-image`
5. Make sure its working `python main.py test-all-async`
