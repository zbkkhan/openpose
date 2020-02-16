docker exec $1 bash -c "rm -rf /openpose/build/examples/fydp && mkdir /openpose/build/examples/fydp"
docker cp fydp3/. $1:/openpose/build/examples/fydp/.
docker exec $1 bash -c "rm -rf /root/.aws && mkdir /root/.aws"
docker cp ~/.aws/. $1:/root/.aws/.
