# ignition

Rewrite of codescord to a webbservice.

Written in python3.9.

## Non python Dependencies

* Docker

## Install and run

If your user does not have access to docker commands 
`python` must be replaced with `venv/bin/python` in the commands using `main.py` and be run using `sudo`.
Otherwise, the process will not have access to docker which is essential for the application to work.

0. Clone: `git clone https://github.com/eliaseriksson/ignition && cd ignition`
1. Create a venv: `python3 -m venv venv`
2. Activate venv: `source venv/bin/activate`
3. Install python dependencies: `python -m pip install -r requirements.txt`
4. Build the Docker image: `python main.py build-docker-image`
5. Make sure its working `python main.py test`
6. Start the webserver: `python main.py server`

## Production comments
There might be better ways of running the application in production.
The server command is only a basic way of getting it to run.
The server can be started with `uvicorn app:app` 
check [fastAPI](https://fastapi.tiangolo.com/deployment/manually/) / [uvicorn](https://www.uvicorn.org/deployment/) docs for better advice on how to run uvicorn in production. 
