from flask import Flask, Response, render_template, request
import json
from subprocess import Popen, PIPE
import os
from tempfile import mkdtemp
from werkzeug import secure_filename

app = Flask(__name__)

@app.route("/")
def index():
    return """
Available API endpoints:
GET /containers                     List all containers
GET /containers?state=running       List running containers (only)
GET /containers/<id>                Inspect a specific container
GET /containers/<id>/logs           Dump specific container logs
GET /images                         List all images
POST /images                        Create a new image
POST /containers                    Create a new container
PATCH /containers/<id>              Change a container's state
PATCH /images/<id>                  Change a specific image's attributes
DELETE /containers/<id>             Delete a specific container
DELETE /containers                  Delete all containers (including running)
DELETE /images/<id>                 Delete a specific image
DELETE /images                      Delete all images
"""

@app.route('/containers', methods=['GET'])
def containers_index():

    """
    List all containers
 
    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/containers | python -mjson.tool
    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/containers?state=running | python -mjson.tool
    """


    if request.args.get('state') == 'running': 
        output = docker('ps')
        resp = json.dumps(docker_ps_to_array(output))
         
    else:
        output = docker('ps', '-a')
        resp = json.dumps(docker_ps_to_array(output))

   
    return Response(response=resp, mimetype="application/json")

@app.route('/images', methods=['GET'])
def images_index():
    imageresult = docker_images_to_array(docker('images'))
    resp = json.dumps(imageresult)
    return Response(response=resp, mimetype="application/json")

#I added the nodes GET
@app.route('/nodes', methods = ['GET'])
def get_nodes():
    #the command for listing nodes is ls
    res = docker_nodes_to_array(docker('node', 'ls'))
    resp = json.dumps(res)
    return Response(response=resp, mimetype="application/json")

#I added the services GET based in the images get
@app.route('/services', methods = ['GET'])
def get_services():
    res = docker_services_to_array(docker('service', 'ls'))
    resp = json.dumps(res)
    return Response(response=resp, mimetype="application/json")

@app.route('/containers/<id>', methods=['GET'])
def containers_show(id):
    #docker inspect can get a certain instances name, so I pass that command in
    resp = docker('inspect', id)
    return Response(response=resp, mimetype="application/json")

@app.route('/containers/<id>/logs', methods=['GET'])
def containers_log(id):
    #command is docker logs and id
    res = docker_logs_to_object(id,docker('logs', id))
    resp = json.dumps(res)
    return Response(response=resp, mimetype="application/json")

@app.route('/images/<id>', methods=['DELETE'])
def images_remove(id):
    resp = docker('rmi', id)
    return Response(response=resp, mimetype="application/json")

@app.route('/containers/<id>', methods=['DELETE'])
def containers_remove(id):
    """
    Delete a specific container - must be already stopped/killed
    curl -s -X DELETE -H 'Content-Type: application/json' http://localhost:8080/containers/b6cd8ea512c8
    """
    #rm command gets rid of a container
    resp = docker('rm', id)
    return Response(response=resp, mimetype="application/json")

@app.route('/containers', methods=['DELETE'])
def containers_remove_all():
    final = docker('ps', '-a')
    #call the method witht the command 
    containers = docker_ps_to_array(final)

    #loop through each container,
    for container in containers:
        docker('stop', container['id'])
    for container in containers:
        docker('rm', container['id'])
    return Response(response='All containers removed', mimetype="application/json")

@app.route('/images', methods=['DELETE'])
def images_remove_all():
    #dont need to feed resp anywhere, it's jsut a string
    final = docker('images')

    #call method
    images = docker_images_to_array(final)
    #loop through to get all of them, using rmi command
    for image in images:
        docker('rmi', image['id'], '-f')
    return Response(response='Removed the images', mimetype="application/json")


@app.route('/containers', methods=['POST'])
def containers_create():
    """
    Create container (from existing image using id or name)
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "my-app"}'
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "b14752a6590e"}'
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "b14752a6590e","publish":"8081:22"}'
    """
    body = request.get_json(force=True)
    image = body['image']
    args = ('run', '-d')
    id = docker(*(args + (image,)))[0:12]
    return Response(response='{"id": "%s"}' % id, mimetype="application/json")


@app.route('/images', methods=['POST'])
def images_create():
    #making an image from the uploaded docker file
    dockerfile = request.files['file']
    dpath = mkdtemp()


    filename = secure_filename(dockerfile.filename)
    #joining the secure file name and the mkdtemp into variable
    path = os.path.join(dpath, filename)
    c_path = os.path.join(dpath, '.')
    dockerfile.save(path)

    resp = docker('build', '-t', filename.lower(), '-f', path, c_path)
    return Response(response=resp, mimetype="application/json")


@app.route('/containers/<id>', methods=['PATCH'])
def containers_update(id):
    """
    Update container attributes (support: state=running|stopped)
    curl -X PATCH -H 'Content-Type: application/json' http://localhost:8080/containers/b6cd8ea512c8 -d '{"state": "running"}'
    curl -X PATCH -H 'Content-Type: application/json' http://localhost:8080/containers/b6cd8ea512c8 -d '{"state": "stopped"}'
    """
    body = request.get_json(force=True)
    try:
        state = body['state']
        if state == 'running':
            docker('restart', id)
    except:
        pass

    resp = '{"id": "%s"}' % id
    return Response(response=resp, mimetype="application/json")

@app.route('/images/<id>', methods=['PATCH'])
def images_update(id):
    patchresult = request.get_json(force=True)
    #docker tag  'tags' and image with a certain id to the a certain repo, in this case, the request
    resp = docker('tag', id, patchresult['tag'])
    return Response(response=resp, mimetype="application/json")


def docker(*args):
    cmd = ['docker']
    for sub in args:
        cmd.append(sub)
    process = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    err = stderr.decode('utf-8')
    out = stdout.decode('utf-8')
    if stderr.startswith(b'Error'):
        print('Error: {0} -> {1}'.format(' '.join(cmd), stderr))
    return stderr + stdout

#changed the image name and port var with decodes because i was getting a type error
def docker_ps_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[0].decode('utf-8')
        each['image'] = c[1].decode('utf-8')
        each['name'] = c[-1].decode('utf-8')
        each['ports'] = c[-2].decode('utf-8')
        all.append(each)
    return all
#similar to getting the nodes but with different service parameters
def docker_services_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[0].decode('utf-8')
        each['name'] = c[1].decode('utf-8')
        each['mode'] = c[2].decode('utf-8')
        each['replicas'] = c[3].decode('utf-8')
        each['image'] = c[4].decode('utf-8')
        all.append(each)
    return all
#I took the structure of ps_to_array to do this method
#but with different variables to hold parts of nodes
def docker_nodes_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[0].decode('utf-8')
        each['hostname'] = c[1].decode('utf-8')
        each['status'] = c[2].decode('utf-8')
        each['available'] = c[3].decode('utf-8')
        all.append(each)
    return all
#
# Parses the output of a Docker logs command to a python Dictionary
# (Key Value Pair object)
def docker_logs_to_object(id, output):
    logs = {}
    logs['id'] = id
    all = []
    for line in output.splitlines():
        all.append(line)
    logs['logs'] = all
    return logs

#
# Parses the output of a Docker image command to a python List
def docker_images_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[2].decode('utf-8')
        each['tag'] = c[1].decode('utf-8')
        each['name'] = c[0].decode('utf-8')
        all.append(each)
    return all

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000, debug=True)
