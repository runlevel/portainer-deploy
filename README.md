# portainer-deploy 
[![supported python versions](https://img.shields.io/badge/python-3.9-blue.svg)](https://artifactory.si.francetelecom.fr/api/pypi/virt-dom-rsx-pypi/simple/swarm_deploy/)

Deploy a compose file to docker-swarm using the portainer API

## Docker image
```shell
$ docker run -ti  
root@44c83b8ff2ee:/# portainer-delploy
2019-11-26 12:12:02,829 - root - INFO - swarm_deploy start...
```

## Usage
- Set the mandatory environment variables
  - **PORTAINER_URL** Portainer endpoint 
  - **PORTAINER_USERNAME** Username to make the calls to the portainer API
  - **PORTAINER_PASSWORD** The password associated with the username 
  - **STACK_NAME** Name of the stack that will be deployed in the swarm cluster
  - **COMPOSE_CONTENT** Content of the docker-compose file as a string
    - Standard docker-compose :
      ```shell
      export COMPOSE_CONTENT=$(cat docker-compose-example.yml)
      ```
    - Jinja2 docker-compose :
      - Use the [j2cli tool](https://github.com/kolypto/j2cli#tutorial-with-environment-variables)
      - Set environment variables for the Jinja2 variables in your compose file [environment variables](https://github.com/kolypto/j2cli#tutorial-with-environment-variables)
      ```shell
      export COMPOSE_CONTENT=$(j2 docker-compose-example.yml.j2)
      ```

### Commands
- Update an existing stack
  ```shell
  portainer-deploy
  ```

- Remove an existing stack
  ```shell
  portainer-deploy --remove
  ```

- Remove an existing stack and redeploy it
  ```shell
  portainer-deploy --remove
  portainer-deploy
  ```

## .gitlab-ci.yml example

```yaml
deploy_stack:
  stage: deploy
  image: 
  variables:
    PORTAINER_URL : https://portainer.mydomain.com
    STACK_NAME : example-stack
    TEST_VARIABLE: "test"
  script:
    - export COMPOSE_CONTENT=$(j2 docker-compose-example.yml.j2)
    - portainer-deploy
```

## Output:
```shell
$ portainer-deploy
```
