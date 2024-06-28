# AssistantsAPI-ReactTS-stream-demo
Project with Flask backend and React Typescript frontend.  Demonstrates the Assistants API streaming from OpenAI.

# Usage
The idea here was to create a very simple Flask server that sends a response that is a streaming data as from the Assistants API as application/stream+json.

# Setup
1.  Create your environment and run the requirements file

2.  pip install -r requirements.txt

3.  Change the env.local to .env

4.  You need to configure the .env wil with your OpenAI key.  

5.  You also need to configure the search variables to point to an Azure Search Index.

6.  Finally edit server.py with a question you want to ask your data.

7.  Run the server.py in the backend directory.

8.  python server.py

9.  The server will start on port 5000.  Now you can simply use curl:

10.  curl localhost:5000

11. Start the react server by cd frontend running yarn build to build then serve -s build to run the build

