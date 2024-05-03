import os
from openai import OpenAI, AssistantEventHandler
from openai.types.beta.threads.runs import ToolCall, RunStep
from backend.tools.searchclient import SearchAzure
import json
from dotenv import load_dotenv
from colorama import Fore, Style
from typing_extensions import override
from colorama import Fore, Style
from queue import Queue
import threading

load_dotenv()

openai_model: str = os.environ.get("OPENAI_MODEL")
assistant_id = os.environ.get("ASSISTANT_ID") # this is the id of a simple assistant that exists in OpenAI
# create client for OpenAI
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
search_client: SearchAzure = SearchAzure()  # get instance of search to query corpus


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
           print(f"calling function: {self.function_name}")

           if self.function_name == "azure_search": # the Assistant knows to use this because of the system prompt in the assistant
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

def print_stream(queue: Queue):     
    while True:
        item = queue.get(block=True)
        if item is None:
            queue.task_done()  # Mark the 'None' item as processed
            break  # Exit the loop as no more items will be added
        print(item, end='', flush=True)
        queue.task_done()  
    

def main():
    assistant_thread_id = openai_client.beta.threads.create()
    while True:
                queue = Queue()   
                # Get user query
                query = input('\n\nQUERY: ').strip()
                if query.lower() == 'exit':
                    exit(0)                    
                try:
                # Retrieve an existing assistant which is Shadow Assistant
                # Here is the System prompt for the Assistant
                
                # You are a helpful assistant.

                # Always call function 'azure_search'. This function provides necessary data for you to answer the USER query.

                # Always return your answers in markdown.

                # [**SOURCE:** <name of functions called during run>]

                    assistant = openai_client.beta.assistants.retrieve(
                                    assistant_id=assistant_id,
                                    )
                    
                    openai_client.beta.threads.messages.create(  # create a message on the thread that is a user message
                                thread_id=assistant_thread_id.id, 
                                role="user",
                                content=query
                                )
                    
                    stream_event_handler = StreamEventHandler(queue, assistant_thread_id.id) 
                    
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
                    #thread.daemon = True  # Daemonize thread to close when main program exits
                    thread.start()
                    
                    print_stream(queue)  # print the stream
                    
                    # Wait for the printer thread to process the None and exit
                    thread.join()
                                        
                except Exception as yikes:
                        print(f'\n\nError communicating with OpenAI: "{yikes}"')
                    
if __name__ == '__main__':
    main()



        
