from flask import Flask, Response, stream_with_context
import json
import os
import time
from flask_cors import CORS
from openai import OpenAI, AssistantEventHandler
from openai.types.beta.threads import Message, MessageDelta
from openai.types.beta.threads.runs import ToolCall, RunStep
from openai.types.beta import AssistantStreamEvent
from tools.searchclient import SearchAzure
from dotenv import load_dotenv
from typing_extensions import override
from queue import Queue, Empty
import threading

load_dotenv()

openai_model: str = os.environ.get("OPENAI_MODEL")
# bing_subscription_key = os.environ.get("BING_SEARCH_KEY")
# create client for OpenAI
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
search_client: SearchAzure = SearchAzure()  # get instance of search to query corpus

app = Flask(__name__)
cors = CORS(app,supports_credentials=True, resources={r"/stream/*": {"origins": "*"}})

# Initialize a global queue
data_queue = Queue()

# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.
class StreamEventHandler(AssistantEventHandler):
    def __init__(self, queue, thread_id):
        super().__init__()
        self.queue = queue
        self.thread_id = thread_id
        self.run_id = None
        self.function_name = ""
        self.arguments = ""

    @override
    #def on_text_created(self, text) -> None:
        #print(f"\nassistant > ", end="", flush=True)
    #    self.queue.put(f"\nassistant > ")

    @override
    def on_text_delta(self, delta, snapshot):
        #print(delta.value, end="", flush=True)
        self.queue.put(delta.value)

    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)

    @override
    def on_run_step_created(self, run_step: RunStep) -> None:
       # 2       
       #print(f"on_run_step_created")
       self.run_id = run_step.run_id
       self.run_step = run_step
       #print("The type of run_step run step is ", type(run_step), flush=True)
       #print(f"\n run step created assistant > {run_step}\n", flush=True)

    def on_tool_call_created(self, tool_call):
       #self.queue.put(f"\nassistant > {tool_call.type}\n")
       # 4
       #print(f"\nassistant on_tool_call_created > {tool_call}")
       self.function_name = tool_call.function.name       
       self.tool_id = tool_call.id
       #print(f"\on_tool_call_created > run_step.status > {self.run_step.status}")
      
       #print(f"\nassistant > {tool_call.type} {self.function_name}\n", flush=True)

       keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
           thread_id=self.thread_id,
           run_id=self.run_id
       )

       while keep_retrieving_run.status in ["queued", "in_progress"]: 
           keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
               thread_id=self.thread_id,
               run_id=self.run_id
           )
          
           #print(f"\nSTATUS: {keep_retrieving_run.status}") 

    @override
    def on_tool_call_done(self, tool_call: ToolCall) -> None:       
       keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
           thread_id=self.thread_id,
           run_id=self.run_id
       )
      
       #print(f"\nDONE STATUS: {keep_retrieving_run.status}")
    
       if keep_retrieving_run.status == "completed":
           all_messages = openai_client.beta.threads.messages.list(
               thread_id=self.thread_id
           )

           print(all_messages.data[0].content[0].text.value, "", "")
           return
      
       elif keep_retrieving_run.status == "requires_action":
           print("here you would call your function")

           if self.function_name == "azure_search":
               function_data = search_client.search_hybrid(query=json.loads(tool_call.function.arguments)["query"])
               self.output=function_data
              
               with openai_client.beta.threads.runs.submit_tool_outputs_stream(
                   thread_id=self.thread_id,
                   run_id=self.run_id,
                   tool_outputs=[{
                       "tool_call_id": self.tool_id,
                       "output": self.output,
                   }],
                   event_handler=StreamEventHandler(self.queue, self.thread_id)
               ) as stream:
                 stream.until_done()                       
           else:
               print("unknown function")
               return

# Function to perform a Shadow Search
def azure_search(query):
    search_result = search_client.search_hybrid(query)
    print(search_result)
    return search_result

def event_stream(queue):
    while True:
        message = queue.get()
        if message is None:  # Use `None` as a signal to end the stream.
            break
         # Serialize the message to JSON. No SSE-specific formatting is required.
        json_message = json.dumps({"message": message})  # Newline as delimiter
        #print(json_message.encode('utf-8'))
        yield json_message.encode('utf-8')

@app.route("/stream")
def stream():
    queue = Queue()
    
    assistant_thread_id = openai_client.beta.threads.create()

    # Define your event handler with the queue
    event_handler = StreamEventHandler(queue, assistant_thread_id.id)

    # Retrieve an existing assistant which is Shadow Assistant
    assistant = openai_client.beta.assistants.retrieve(
        assistant_id="asst_g21JvXjw8tM9oVW8dqNFa3yb",
    )

    openai_client.beta.threads.messages.create(  # create a message on the thread that is a user message
        thread_id=assistant_thread_id.id,
        role="user",
        content="What are different strategies I should be considering when approaching a new prospect where we are unfamiliar and they are in the early stages of demand?",
    )

    # Start the API call in a separate thread
    def start_api_call():
        with openai_client.beta.threads.runs.create_and_stream(
            thread_id=assistant_thread_id.id,
            assistant_id=assistant.id,
            event_handler=event_handler,
        ) as stream:
            stream.until_done()
        queue.put(None)  # Signal the end of the stream

    thread = threading.Thread(target=start_api_call)
    thread.start()

    return Response(event_stream(queue), mimetype="application/stream+json")

if __name__ == "__main__":
    app.run(debug=True)
