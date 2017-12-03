#creating a docker image
curl -H 'Accept: application/json' -F "file=@dockerfiles/whale-say.Dockerfile" http://35.195.27.0:5000/images

#creating a docker container
curl -X POST -H "Content-Type: application/json" http://35.195.27.0:5000/containers -d '{"image": "dockersamples/visualizer:latest"}'

#get all containers
curl -s -X GET -H 'Accept: application/json' http://http://35.195.27.0:5000/containers

#get all containers that are running
curl -s -X GET -H 'Accept: application/json' http://35.195.27.0:5000/containers?state=running

#change container state
curl -X PATCH -H "Content-Type: application/json" http://35.195.27.0:5000/containers/69a8dd28c359 -d '{"state": "running"}'
curl -X PATCH -H "Content-Type: application/json" http://35.195.27.0:5000/containers/69a8dd28c359 -d '{"state": "stopped"}'

#change image tag
curl -s -X PATCH -H curl -X PATCH -H "Content-Type: application/json" http://35.195.27.0:5000/images/656c72e5b88f -d '{"tag": "test:1.1"}'

#del container by its id
curl -s -X DELETE -H "Content-Type: application/json" http://35.195.27.0:5000/containers/e5b8193b0834

#del image by its id
curl -s -X DELETE -H "Content-Type: application/json" http://35.195.27.0:5000/images/8e603db2581b

#del all containers
curl -s -X DELETE -H 'Accept: application/json' http://35.195.27.0:5000/containers

#del all images 
curl -s -X DELETE -H 'Accept: application/json' http://35.195.27.0:5000/images
