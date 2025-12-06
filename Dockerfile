FROMpython:3.11.9-slim

ENVPYTHONDONTWRITEBYTECODE=1
ENVPYTHONUNBUFFERED=1
ENVPORT=8080
ENVHOST=0.0.0.0

WORKDIR/app

RUNapt-getupdate&&apt-getinstall-y--no-install-recommends \
build-essential \
gcc \
curl \
&&rm-rf/var/lib/apt/lists/*

COPYrequirements.txt/requirements.txt
RUNpipinstall--no-cache-dir--upgradepip&&pipinstall--no-cache-dir-r/requirements.txt

COPY.

EXPOSE8080

CMDsh-c"if[-f main.py];thenpython main.py;elif[-f app.py];thenpython app.py;elif[-f server.py];thenpython server.py;elsepython -m uvicorn main:app --host 0.0.0.0 --port ${PORT};fi"
