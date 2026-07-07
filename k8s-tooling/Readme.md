general:
echo "10.43.63.81 s3.example.com" >> /etc/hosts

elbencho:
elbencho --s3endpoints "http://s3.example.com:80" --s3key="jNqqsAJLhkBVDyAtP5jc" --s3secret="PXOlKYBNrcE8n+CLnQcwUg8O0Kp9wxf/RmuFLTB4" -w -t 1 -s 16g -b 16m "jantest/bigobjects/file[1-256]"

warp:
./warp put --host=s3.example.com:80 --access-key=jNqqsAJLhkBVDyAtP5jc --secret-key=PXOlKYBNrcE8n+CLnQcwUg8O0Kp9wxf/RmuFLTB4 --bucket=jantest


mc:
mc alias set jantest http://s3.example.com:80 jNqqsAJLhkBVDyAtP5jc PXOlKYBNrcE8n+CLnQcwUg8O0Kp9wxf/RmuFLTB4 
mc ls jantest
mc mb jantest/jannochntest
mc cp /etc/passwd jantest/jannochntest/

