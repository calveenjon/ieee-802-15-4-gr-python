#!/bin/bash

rm -rf build/
mkdir build

pushd build
cmake -DCMAKE_BUILD_TYPE=Debug ../
make -j8

sudo make install
sudo ldconfig
popd

exit 0