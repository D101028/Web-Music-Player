cd /data/data/com.termux/files/home/Projects/Web-Music-Player
. .venv/bin/activate
[ -d ./log ] || mkdir ./log
[ -f ./log/.pid ] && kill $(cat ./log/.pid) && rm ./log/.pid
> ./log/.pid
nohup python main.py -c test.conf > ./log/log.txt 2>&1 & echo $! >> ./log/.pid
