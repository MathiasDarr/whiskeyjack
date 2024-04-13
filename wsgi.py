from whiskeyjack_upload.app import create_app
import os

"""
    Instructs flask or other wsgi service how to initialize the web app
"""
docker = os.getenv("EPHEMERAL_DOCKER", "none")
application = create_app(docker)

if __name__ == "__main__":
    host = 8080
    port = 8080
    debugging = application.config["DEBUG"]
    application.run(host=host, port=port, debug=debugging)
