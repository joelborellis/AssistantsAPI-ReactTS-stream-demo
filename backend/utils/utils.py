import json
import functools
import asyncio
import time
from datetime import datetime


def timeit_decorator(func):
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        # Retrieve model from kwargs if present; default to None if not
        print(f"kwargs passed to the function:  {kwargs}")
        #model = kwargs.get("model", None)
        #prompt = kwargs.get("prompt", None)
        #async_wrapper.model = model  # Assign model to wrapper attribute, defaulting to None if not provided
            
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = round(end_time - start_time, 4)

        # `args[0]` refers to the instance (`self`) of the tool class
        instance = args[0] if len(args) > 0 else None
        #description = getattr(instance, "description", func.__name__)
        name = getattr(instance, "name", func.__name__)
        
        print(f"⏰ {name}() took {duration:.4f} seconds")
        
        # Prepare to log the model usage
        #model_name = model_name_to_id.get(async_wrapper.model, "unknown")

        jsonl_file = "./run_timeit_async.json"

        # Create new time record
        time_record = {
            "timestamp": datetime.now().isoformat(),
            "function": name,
            #"prompt": prompt,
            "duration": f"{duration:.4f}",
            #"model": f"{async_wrapper.model} - {model_name}",
        }

        # Append the new record to the JSONL file
        with open(jsonl_file, "a") as file:
            json.dump(time_record, file)
            file.write("\n")

        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        print(f"kwargs passed to the function:  {kwargs}")
        # Retrieve model from kwargs if present; default to None if not
        #model = kwargs.get("model", None)
        #async_wrapper.model = model  # Assign model to wrapper attribute, defaulting to None if not provided
            
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = round(end_time - start_time, 4)
        print(f"⏰ {func.__name__}() took {duration:.4f} seconds")
        
        # Prepare to log the model usage
        #model_name = model_name_to_id.get(async_wrapper.model, "unknown")

        jsonl_file = "./run_timeit.json"

        # Create new time record
        time_record = {
            "timestamp": datetime.now().isoformat(),
            "function": func.__name__,
            "duration": f"{duration:.4f}",
            #"model": f"{sync_wrapper.model} - {model_name}",
        }

        # Append the new record to the JSONL file
        with open(jsonl_file, "a") as file:
            json.dump(time_record, file)
            file.write("\n")

        return result

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper