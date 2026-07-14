general:
echo "10.43.115.67 s3.example.com" >> /etc/hosts

elbencho:
# S3 benchmark
elbencho --s3endpoints "http://quobyte-s3.quobyte.svc.cluster.local:80" --s3key="XXXXjjDBaJzBZg9GbB0X" --s3secret="XXXX1YPBS2HRef9DDawqQ8K1OrGhy93eGHV91uF" -r -w -F -t 16 -s 250m -b 1m "jantest/bigobjects/file[1-2560]"
# Similar settings for filesystem benchmark
elbencho -F -r -w -t 8 -s 250m -b 1m /mnt/quobyte-volume/bigobjects/file[1-2560]

warp:
./warp put --host=s3.example.com:80 --access-key=XXXqsAJLhkBVDyAtP5jc --secret-key=XXXlKYBNrcE8n+CLnQcwUg8O0Kp9wxf/RmuFLTB4 --bucket=jantest


mc:
mc alias set jantest http://s3.example.com:80 XXXqsAJLhkBVDyAtP5jc XXXlKYBNrcE8n+CLnQcwUg8O0Kp9wxf/RmuFLTB4 
mc ls jantest
mc mb jantest/jannochntest
mc cp /etc/passwd jantest/jannochntest/

s3cmd:
s3cmd --no-check-certificate ls  s3://jantest --host=quobyte-s3.quobyte.svc.cluster.local --host-bucket="http://%(bucket).quobyte-s3.quobyte.svc.cluster.local" --access_key=XXXXjjDBaJzBZg9GbB0X --secret_key=XXXX01YPBS2HRef9DDawqQ8K1OrGhy93eGHV91uF --no-ssl
