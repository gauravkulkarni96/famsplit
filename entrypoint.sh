#!/bin/bash

python manage.py migrate        # Apply database migrations
python manage.py initadmin      # Create admin user if no user exists

# directory for gunicorn logs and django app logs
rm -rf $DOCKYARD_SRVPROJ/logs
mkdir -p $DOCKYARD_SRVPROJ/logs
touch $DOCKYARD_SRVPROJ/logs/famsplit.log
tail -n 0 -f $DOCKYARD_SRVPROJ/logs/famsplit.log &

echo Starting Django runserver.
python manage.py runserver 0.0.0.0:8000
