# Configuring the surface station

Surface station is a cross-platform centre for operating the underwater vehicle remotely. As it's entirely based on the *Python* programming language, it should be compatible with any device able to use it.

## Modifications

Here is a full list of changes introduced to the system. Naturally, before installing any of them you should `update` and `upgrade` your system via `apt-get`.

1. `Python3.6` installation
2. *Python* libraries installation via `pip`
3. `OpenCV` installation (pending)

### Python3.6 installation

Follow instructions at https://www.python.org/downloads and install `Python3.6.4`

### Python libraries installation via `pip`

Run the following block of commands:

```commandline
sudo python3.6 -m pip install --upgrade pip
sudo python3.6 -m pip install diskcache
sudo python3.6 -m pip install pyserial
sudo python3.6 -m pip install pathos
sudo python3.6 -m pip install inputs
sudo python3.6 -m pip install numba
sudo python3.6 -m pip install PySide2
```

### OpenCV installation (pending)

To be tested.