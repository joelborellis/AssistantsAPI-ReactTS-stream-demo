from flask import Flask, Response
import json
import os
import time
from flask_cors import CORS
from openai import OpenAI, AssistantEventHandler
from openai.types.beta.threads.runs import ToolCall, RunStep
from backend.tools.searchshadow import SearchShadow
from backend.tools.searchcustomer import SearchCustomer
from dotenv import load_dotenv
from typing_extensions import override
from queue import Queue
import threading

load_dotenv()

openai_model: str = os.environ.get("OPENAI_MODEL")
# bing_subscription_key = os.environ.get("BING_SEARCH_KEY")
# create client for OpenAI
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
search_client: SearchShadow = SearchShadow()  # get instance of search to query corpus
search_client_customer: SearchCustomer = (
    SearchCustomer()
)  # get instance of search to query corpus

app = Flask(__name__)
cors = CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

def save_file_json(filename, data):
    """
    Save the given data as JSON in a file.

    Parameters:
    filename (str): The name of the file to write to (e.g., 'output.json').
    data (dict or list or any JSON-serializable object): The data to be saved.
    """
    # Ensure the filename ends with .json for clarity
    if not filename.endswith('.json'):
        filename += '.json'

    # Write the data to the JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Function to perform a Search of an Azure Search index
def azure_search(query):
    search_result = search_client.search_hybrid(query)
    # print(search_result)
    return search_result


def azure_search_customer(customer, query):
    print(f"Prospect Name: {customer} - Search context:  {query}")
    search_result = search_client_customer.search_hybrid(customer + query)
    # print(search_result)
    return search_result


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

    override

    def on_event(self, event):
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == "thread.run.requires_action":
            print(f"event:  {event.event}")

            self.run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, self.run_id)

    def handle_requires_action(self, data, run_id):
        tool_outputs = []

        for tool in data.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "search_shadow":
                function_data = azure_search(
                    query=json.loads(tool.function.arguments)["query"]
                )
                # self.output = function_data
                print(f"search_shadow_id:  {tool.id}")
                tool_outputs.append({"tool_call_id": tool.id, "output": function_data})

            elif tool.function.name == "search_customer":
                function_data = azure_search_customer(
                    customer=json.loads(tool.function.arguments)["customer"],
                    query=json.loads(tool.function.arguments)["query"],
                )
                # self.output = function_data
                print(f"search_customer_id:  {tool.id}")
                tool_outputs.append({"tool_call_id": tool.id, "output": function_data})

        # Submit all tool_outputs at the same time
        #save_file_json("run.json", tool_outputs)
        self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with openai_client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs,
            event_handler=StreamEventHandler(self.queue, self.thread_id),
        ) as stream:
            stream.until_done()

    def on_text_delta(
        self, delta, snapshot
    ):  # this is where the actual streamed response gets packed into the queue
        # print(delta.value, end="", flush=True)
        self.queue.put(delta.value)


def event_stream(queue):
    while True:
        message = queue.get()
        if message is None:  # Use `None` as a signal to end the stream.
            break
        # Serialize the message to JSON. No SSE-specific formatting is required.
        json_message = json.dumps({"message": message})
        json_message.encode("utf-8")
        # print(json_message, end="", flush=True)
        yield f"{json_message}\n\n"


@app.route("/")
def stream():
    queue = Queue()

    assistant_thread_id = openai_client.beta.threads.create()

    # Define your event handler with the queue
    stream_event_handler = StreamEventHandler(queue, assistant_thread_id.id)

    # Retrieve an existing assistant which is a generic Assistant that has a function called azure_search
    assistant = openai_client.beta.assistants.retrieve(
        assistant_id="asst_g21JvXjw8tM9oVW8dqNFa3yb",
    )

    openai_client.beta.threads.messages.create(  # create a message on the thread that is a user message
        thread_id=assistant_thread_id.id,
        role="user",
        content='I am in the discovery phase with a customer Northhiighland, can you suggest ways to proceed with engaging with the customer?',
    )

    # Start the API call in a separate thread
    def start_api_call():
        with openai_client.beta.threads.runs.stream(
            thread_id=assistant_thread_id.id,
            assistant_id=assistant.id,
            event_handler=stream_event_handler,
        ) as stream:
            stream.until_done()
        queue.put(None)  # Signal the end of the stream

    thread = threading.Thread(target=start_api_call)
    thread.start()

    return Response(event_stream(queue), mimetype="application/stream+json")


if __name__ == "__main__":
    app.run(debug=True)
