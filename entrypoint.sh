#!/bin/bash
set -e

chown -R shux:shux /home/shux/app/static/images/maps

exec "$@"