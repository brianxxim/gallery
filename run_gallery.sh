#! /bin/bash
# shellcheck disable=SC1090
source ~/.bash_profile
workon gallery
export DJANGO_SETTINGS_MODULE=photoshare.settings
export DJANGO_DEBUG=False
cd /web/projects/gallery || echo "gallery project non-existent"
exec uwsgi --ini uwsgi.ini
