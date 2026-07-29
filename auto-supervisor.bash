sudo rm /etc/supervisor/conf.d/*
sudo cp hwoj.conf/hwoj-* /etc/supervisor/conf.d
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all