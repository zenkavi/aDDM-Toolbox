
# Minimal Container

Build container

```
docker build -t zenkavi/addm-toolbox:0.0.3 -f ./Dockerfile .
```

Push container

```
docker push zenkavi/addm-toolbox:0.0.3
```

Pull container

```
docker pull zenkavi/addm-toolbox:0.0.3
```

Run container without display

```
docker run --rm -it -v ${PWD}:/home/aDDM-Toolbox zenkavi/addm-toolbox:0.0.3 bash
```

Add display to docker image for plots **on MAC** (Thanks to notes from [here](https://gist.github.com/cschiewek/246a244ba23da8b9f0e7b11a68bf3285))

```
export HOSTNAME=`hostname`
xhost +${HOSTNAME}
docker run --rm -ti -v /tmp/.X11-unix:/tmp/.X11-unix -e "DISPLAY=${HOSTNAME}:0" -v ${PWD}:/home/aDDM-Toolbox zenkavi/addm-toolbox:0.0.3 bash
```

# TBD Notebook Container

See `addm_nb.Dockerfile` that is currently breaking.

```
Successfully built future numpy matplotlib addm_toolbox
Failed to build pandas scipy
```