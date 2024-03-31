import os
import openai
import time
from openai import OpenAI, AssistantEventHandler
from openai.types.beta.threads import Message, MessageDelta
from openai.types.beta.threads.runs import ToolCall, ToolCallDelta, RunStep
from openai.types.beta import AssistantStreamEvent
from backend.tools.searchclient import SearchShadow
import json
from dotenv import load_dotenv
from colorama import Fore, Back, Style
from flask import Response, stream_with_context
from typing_extensions import override
from colorama import Fore, Back, Style

load_dotenv()

openai_model: str = os.environ.get("OPENAI_MODEL")
#bing_subscription_key = os.environ.get("BING_SEARCH_KEY")
# create client for OpenAI
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
search_client: SearchShadow = SearchShadow()  # get instance of search to query corpus

###     file operations

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()
    
# create a json object that can be used as the response   
def create_json_object(id, message_content):
        json_object = {
            "thread_id": id,
            "message": message_content,
        }
        return json.dumps(json_object, indent=2)
        
###     API functions
# Function to perform a Shadow Search
def shadow_search(query):
    search_result = search_client.search_hybrid(query)
    print(search_result)
    return search_result

 
# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.
 
class EventHandler(AssistantEventHandler):
   def __init__(self, thread_id, assistant_id):
       super().__init__()
       self.output = None
       self.tool_id = None
       self.thread_id = thread_id
       self.assistant_id = assistant_id
       self.run_id = None
       self.run_step = None
       self.function_name = ""
       self.arguments = ""
       self.last_text_delta = None  # Storage for the last text delta
       
   @override
   def on_text_created(self, text) -> None:
       print(Fore.RED + f"\nassistant on_text_created > ", end="", flush=True)
       print(Style.RESET_ALL)

   @override
   def on_text_delta(self, delta, snapshot):
       # print(f"\nassistant on_text_delta > {delta.value}", end="", flush=True)
       print(Fore.GREEN + f"{delta.value}")
       print(Style.RESET_ALL)
       self.last_text_delta = delta.value

   @override
   def get_last_text_delta(self):
        # Method to retrieve the stored last text delta
        return self.last_text_delta
   
   @override
   def on_end(self, ):
       print(f"\n end assistant > ",self.current_run_step_snapshot, end="", flush=True)

   @override
   def on_exception(self, exception: Exception) -> None:
       """Fired whenever an exception happens during streaming"""
       print(f"\nassistant > {exception}\n", end="", flush=True)

   @override
   def on_message_created(self, message: Message) -> None:
       print(f"\nassistant on_message_created > {message}\n", end="", flush=True)

   @override
   def on_message_done(self, message: Message) -> None:
       print(f"\nassistant on_message_done > {message}\n", end="", flush=True)

   @override
   def on_message_delta(self, delta: MessageDelta, snapshot: Message) -> None:
       # print(f"\nassistant on_message_delta > {delta}\n", end="", flush=True)
       pass

   def on_tool_call_created(self, tool_call):
       # 4
       print(f"\nassistant on_tool_call_created > {tool_call}")
       self.function_name = tool_call.function.name       
       self.tool_id = tool_call.id
       print(f"\on_tool_call_created > run_step.status > {self.run_step.status}")
      
       print(f"\nassistant > {tool_call.type} {self.function_name}\n", flush=True)

       keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
           thread_id=self.thread_id,
           run_id=self.run_id
       )

       while keep_retrieving_run.status in ["queued", "in_progress"]: 
           keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
               thread_id=self.thread_id,
               run_id=self.run_id
           )
          
           print(f"\nSTATUS: {keep_retrieving_run.status}")      
      
   @override
   def on_tool_call_done(self, tool_call: ToolCall) -> None:       
       keep_retrieving_run = openai_client.beta.threads.runs.retrieve(
           thread_id=self.thread_id,
           run_id=self.run_id
       )
      
       print(f"\nDONE STATUS: {keep_retrieving_run.status}")
      
       if keep_retrieving_run.status == "completed":
           all_messages = openai_client.beta.threads.messages.list(
               thread_id=self.thread_id
           )

           #print(all_messages.data[0].content[0].text.value, "", "")
           return
      
       elif keep_retrieving_run.status == "requires_action":
           print("here you would call your function")

           if self.function_name == "shadow_search":
               function_data = search_client.search_hybrid(query=json.loads(tool_call.function.arguments)["query"])
               self.output=function_data
              
               with openai_client.beta.threads.runs.submit_tool_outputs_stream(
                   thread_id=self.thread_id,
                   run_id=self.run_id,
                   tool_outputs=[{
                       "tool_call_id": self.tool_id,
                       "output": self.output,
                   }],
                   event_handler=EventHandler(self.thread_id, self.assistant_id)
               ) as stream:
                 stream.until_done()                       
           else:
               print("unknown function")
               return
   @override
   def on_run_step_created(self, run_step: RunStep) -> None:
       # 2       
       print(f"on_run_step_created")
       self.run_id = run_step.run_id
       self.run_step = run_step
       print("The type of run_step run step is ", type(run_step), flush=True)
       print(f"\n run step created assistant > {run_step}\n", flush=True)

   @override
   def on_run_step_done(self, run_step: RunStep) -> None:
       print(f"\n run step done assistant > {run_step}\n", flush=True)

   def on_tool_call_delta(self, delta, snapshot): 
       if delta.type == 'function':
           # the arguments stream thorugh here and then you get the requires action event
           print(delta.function.arguments, end="", flush=True)
           self.arguments += delta.function.arguments
       elif delta.type == 'code_interpreter':
           print(f"on_tool_call_delta > code_interpreter")
           if delta.code_interpreter.input:
               print(delta.code_interpreter.input, end="", flush=True)
           if delta.code_interpreter.outputs:
               print(f"\n\noutput >", flush=True)
               for output in delta.code_interpreter.outputs:
                   if output.type == "logs":
                       print(f"\n{output.logs}", flush=True)
       else:
           print("ELSE")
           print(delta, end="", flush=True)

   @override
   def on_event(self, event: AssistantStreamEvent) -> None:
       # print("In on_event of event is ", event.event, flush=True)

       if event.event == "thread.run.requires_action":
           print("\nthread.run.requires_action > submit tool call")
           print(f"ARGS: {self.arguments}")

if __name__ == '__main__':
    assistant_thread_id = openai_client.beta.threads.create()
    while True:
            # Get user query
            query = input('\n\nQUERY: ').strip()
            if query.lower() == 'exit':
                exit(0)
                    
            try:
            # Retrieve an existing assistant which is Shadow Assistant
                assistant = openai_client.beta.assistants.retrieve(
                                assistant_id="asst_CDgesnP9G5fWP15UVBeQQfUX",
                                )
                
                openai_client.beta.threads.messages.create(  # create a message on the thread that is a user message
                            thread_id=assistant_thread_id.id, 
                            role="user",
                            content=query
                            )
                
                stream_event_handler = EventHandler(assistant_thread_id.id, assistant.id)  

                with openai_client.beta.threads.runs.create_and_stream(
                        thread_id=assistant_thread_id.id,
                        assistant_id=assistant.id,
                        event_handler=stream_event_handler,
                        ) as stream:
                            stream.until_done()

                # After the stream is done, access the last text delta from the event handler
                last_delta = stream_event_handler.on_text_delta
                print(Fore.CYAN + f"\n\n\nLast text delta: {last_delta}")
                print(Style.RESET_ALL)

            except Exception as yikes:
                    print(f'\n\nError communicating with OpenAI: "{yikes}"')



        
