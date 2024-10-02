"""
Deploy a compose file to docker-swarm using the Portainer API.

This script deploys a compose file to Docker Swarm using the Portainer API.
It can also remove an existing stack if the '--remove' argument is provided.

The script requires the following environment variables:
- PORTAINER_URL: The URL of the Portainer instance
- PORTAINER_USERNAME: The username to authenticate with
- PORTAINER_PASSWORD: The password to authenticate with
- STACK_NAME: The name of the stack to deploy
- COMPOSE_CONTENT: The content of the compose file to deploy

Example usage:
    python portainer-deploy.py
    python portainer-deploy.py --remove
"""

import json
import logging
import os
import urllib3
import sys
import requests


class PortainerSwarmDeployer:
    """Class to handle the deployment of compose files to Docker Swarm using the Portainer API."""

    def __init__(self):
        """Initialize session, logging, and essential parameters."""
        self.setup_logging()
        self.session = self.setup_session()
        self.parameters = {
            "PORTAINER_URL",
            "PORTAINER_USERNAME",
            "PORTAINER_PASSWORD",
            "STACK_NAME",
            "COMPOSE_CONTENT",
        }
        self.portainer_url = os.getenv("PORTAINER_URL")
        self.portainer_username = os.getenv("PORTAINER_USERNAME")
        self.portainer_password = os.getenv("PORTAINER_PASSWORD")
        self.stack_name = os.getenv("STACK_NAME")
        self.compose_content = os.getenv("COMPOSE_CONTENT")
        self.portainer_endpoint = f"{self.portainer_url}/api"
        self.remove = False

    def setup_logging(self):
        """Configure logging for the deployer."""
        self.log = logging.getLogger()
        self.log.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

    @staticmethod
    def setup_session():
        """Set up HTTP session with SSL verification and warnings disabled."""
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session = requests.Session()
        session.verify = "/etc/ssl/certs/ca-certificates.crt"
        return session

    def validate_environment(self):
        """Validate necessary environment variables."""
        if self.remove:
            self.parameters.remove("COMPOSE_CONTENT")
        for var in self.parameters:
            if os.getenv(var) is None:
                self.log.critical(f"'{var}' must be set as an environment variable!")
                sys.exit(1)

    def get_portainer_token(self):
        """Authenticate and retrieve the JWT token from the Portainer API."""
        self.log.info("Getting JWT token...")
        response = self.session.post(
            f"{self.portainer_endpoint}/auth",
            json={
                "username": self.portainer_username,
                "password": self.portainer_password,
            },
        )
        response.raise_for_status()
        return response.json()["jwt"]

    def get_endpoint_id(self, token):
        """Retrieve the endpoint ID for the Docker Swarm."""
        response = self.session.get(
            f"{self.portainer_endpoint}/endpoints",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()[0]["Id"]

    def get_swarm_id(self, token, endpoint_id):
        """Retrieve the Swarm ID for the Docker Swarm."""
        response = self.session.get(
            f"{self.portainer_endpoint}/endpoints/{endpoint_id}/docker/swarm",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()["ID"]

    def get_stacks(self, token, endpoint_id):
        """Retrieve the list of deployed stacks."""
        response = self.session.get(
            f"{self.portainer_endpoint}/stacks?endpointId={endpoint_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return {stack["Name"]: {"id": stack["Id"]} for stack in response.json()}

    def remove_stack(self, token, stack_dict, endpoint_id):
        """Remove an existing stack if present."""

        if self.stack_name in stack_dict:
            stack_info = stack_dict[self.stack_name]
            self.log.info(f"Removing stack '{self.stack_name}'")

            response = self.session.delete(
                f"{self.portainer_endpoint}/stacks/{stack_info['id']}?endpointId={endpoint_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            self.log.info(f"Stack '{self.stack_name}' was successfully removed!")
            sys.exit(0)
        else:
            self.log.critical(
                f"Stack '{self.stack_name}' is not deployed! (can't be removed)"
            )
            sys.exit(1)

    def update_stack(self, token, stack_info, endpoint_id, swarm_id):
        """Update an existing stack."""
        self.log.info(f"Updating stack '{self.stack_name}'")
        response = self.session.put(
            f"{self.portainer_endpoint}/stacks/{stack_info['id']}?endpointId={endpoint_id}",
            headers={"Authorization": f"Bearer {token}"},
            data=json.dumps(
                {
                    "Name": self.stack_name,
                    "SwarmID": swarm_id,
                    "StackFileContent": self.compose_content,
                    "Prune": True,
                }
            ),
        )
        self.log.info(response.json())
        response.raise_for_status()
        self.log.info(f"Stack '{self.stack_name}' was successfully updated!")

    def create_stack(self, token, endpoint_id, swarm_id):
        """Create a new stack."""
        self.log.info(f"Creating stack '{self.stack_name}'")
        response = self.session.post(
            f"{self.portainer_endpoint}/stacks?type=1&method=string&endpointId={endpoint_id}",
            headers={"Authorization": f"Bearer {token}"},
            data=json.dumps(
                {
                    "Name": self.stack_name,
                    "StackFileContent": self.compose_content,
                    "SwarmID": swarm_id,
                }
            ),
        )
        self.log.info(response.json())
        response.raise_for_status()
        self.log.info(f"Stack '{self.stack_name}' was successfully created!")

    def deploy(self):
        """Main function to handle the deployment or removal of stacks."""
        self.log.info("Swarm deployment process started...")

        # Validate arguments
        if len(sys.argv) > 2:
            self.log.critical("Only the '--remove' argument is allowed")
            sys.exit(1)

        if len(sys.argv) == 2:
            if sys.argv[1] != "--remove":
                self.log.critical("Only the '--remove' argument is allowed")
                sys.exit(1)
            self.remove = True

        # Validate environment variables
        self.validate_environment()

        # Get Portainer token and other necessary IDs
        token = self.get_portainer_token()
        endpoint_id = self.get_endpoint_id(token)
        swarm_id = self.get_swarm_id(token, endpoint_id)
        stacks = self.get_stacks(token, endpoint_id)

        # Deploy or remove the stack
        if self.remove:
            self.remove_stack(token, stacks, endpoint_id)
        elif self.stack_name in stacks:
            self.update_stack(token, stacks[self.stack_name], endpoint_id, swarm_id)
        else:
            self.create_stack(token, endpoint_id, swarm_id)

        self.log.info("Swarm deployment process completed!")


def main():
    deployer = PortainerSwarmDeployer()
    deployer.deploy()


if __name__ == "__main__":
    main()
