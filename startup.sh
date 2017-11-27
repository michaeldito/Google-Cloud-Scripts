#! /bin/bash
# This is a startup script that will be executed upon startup by any REST server created by scale.py
sudo FLASK_APP=/opt/restserver/restserver.py flask run --host=0.0.0.0 --port=80 &
