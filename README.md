# QuantXchange

## Getting started

### Backend
Set up a virtual environment

    python3 -m venv .venv

Activate the virtual environment

    source .venv/bin/activate

Install the dependencies

    python3 -m pip install -r requirements.txt

To update dependencies of the application

    python -m pip freeze > requirements.txt

To deactivate the virtual environment

    deactivate
    
Start Strapi in watch mode. (Changes in Strapi project files will trigger a server restart)   
    
    yarn develop
  
Start Strapi without watch mode.

    yarn start
  
Build Strapi admin panel.

    yarn build
  
Display all available commands. 

    yarn strapi
     
