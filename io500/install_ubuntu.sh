# install requirements
cd /quobyte/io500-bin/
mkdir io500
cd io500
sudo apt install build-essential dh-autoreconf pkg-config m4 libtool automake openmpi-bin mpi-default-dev
# clone main branch
git clone https://github.com/IO500/io500.git
cd io500
# check out to sc24 tag
##git checkout io500-sc25
./prepare.sh
make

/quobyte/io500-bin/io500/io500/io500 --list > /quobyte/io500-bin/fullconfig.ini
sed -i s#./datafiles#/quobyte/io500-data#g /quobyte/io500-bin/fullconfig.ini 

echo mpirun  --hostfile /quobyte/io500-bin/io500-clients.list /quobyte/io500-bin/io500/io500/io500 /quobyte/io500-bin/fullconfig.ini


