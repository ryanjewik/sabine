figma prototype link: https://www.figma.com/design/FbJGgsLIaidxzPkjHDsrwv/valorant-chatbot-app?node-id=0-1&m=dev


amazon sage maker
us-west-2
domains on the left toolbar
create domain for single user (I will deal with trying to set one up for the organization once I have the time)
click into domain
go to users
create a user if needed with default settings
click launch, then studio
click jupyterlabs on the left
open a workspace (you might have to make one)
go to terminal and clone repo into workspace

1. cd into "flask-server"
2. run ".\venv\Scripts\Activate.ps1"
3. run "python server.py"
4. cd into "client"
5. run "npm start"


additional packages needed to install:
 - npm install axios
 - npm install @mui/material @emotion/react @emotion/styled
 - npm install @mui/material @mui/styled-engine-sc styled-components
 - pip install flask-cors
 - pip install pymongo
 - pip install psycopg2
 - pip install argon2-cffi
 - pip install requests
 - pip install beautifulsoup4
 - pip install langchain
 - python -m pip install "pymongo[srv]"
 - langchain_mongodb
 - langchain_openai
 - langgraph
 - pip install langchain langchain-core langchain-community langchain-openai


sometimes when installing npm packages it breaks everything, run the following to fix:
 - npm audit
 - npm audit fix --force
 - Remove-Item -Recurse -Force node_modules, package-lock.json
 - npm install


extra fixes:
 - e:\sabine\.venv\Scripts\python.exe -m pip install pymongo
