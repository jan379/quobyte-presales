# install requirements
sudo apt install build-essential dh-autoreconf pkg-config m4 libtool automake openmpi-bin mpi-default-dev
# clone main branch
git clone https://github.com/IO500/io500.git
cd io500
# check out to sc24 tag
git checkout io500-sc24
./prepare.sh
make

