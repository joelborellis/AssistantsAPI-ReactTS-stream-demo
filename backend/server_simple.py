from flask import Flask, Response, stream_with_context
import json
import os
import time
from flask_cors import CORS
from openai import OpenAI, AssistantEventHandler
from openai.types.beta.threads import Message, MessageDelta
from openai.types.beta.threads.runs import ToolCall, RunStep
from openai.types.beta import AssistantStreamEvent
from tools.searchclient import SearchShadow
from dotenv import load_dotenv
from typing_extensions import override
from queue import Queue, Empty
import threading

load_dotenv()

openai_model: str = os.environ.get("OPENAI_MODEL")
# bing_subscription_key = os.environ.get("BING_SEARCH_KEY")
# create client for OpenAI
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
search_client: SearchShadow = SearchShadow()  # get instance of search to query corpus

app = Flask(__name__)
cors = CORS(app,supports_credentials=True, resources={r"/stream/*": {"origins": "*"}})

# Initialize a global queue
data_queue = Queue()

# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.


class StreamEventHandler(AssistantEventHandler):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

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


def event_stream(queue):
    while True:
        message = queue.get()
        if message is None:  # Use `None` as a signal to end the stream.
            break
         # Serialize the message to JSON. No SSE-specific formatting is required.
        json_message = json.dumps({"message": message})  # Newline as delimiter
        print(json_message.encode('utf-8'))
        yield json_message.encode('utf-8')


# Function to perform a Shadow Search
def shadow_search(query):
    search_result = search_client.search_hybrid(query)
    print(search_result)
    return search_result


@app.route("/stream")
def stream():
    queue = Queue()
    # Define your event handler with the queue
    event_handler = StreamEventHandler(queue)

    assistant_thread_id = openai_client.beta.threads.create()
    # Retrieve an existing assistant which is Shadow Assistant
    assistant = openai_client.beta.assistants.retrieve(
        assistant_id="asst_g21JvXjw8tM9oVW8dqNFa3yb",
    )

    openai_client.beta.threads.messages.create(  # create a message on the thread that is a user message
        thread_id=assistant_thread_id.id,
        role="user",
        content="What is artificial intelligence?",
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
