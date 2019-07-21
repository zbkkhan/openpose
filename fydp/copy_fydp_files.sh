docker exec $1 bash -c "rm -rf /openpose/build/examples/fydp && mkdir /openpose/build/examples/fydp"
docker cp fydp/. $1:/openpose/build/examples/fydp/.
