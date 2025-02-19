import asyncio
from absl import app, flags
import logging
import glob
import os
import sys
import pickle
import readline

from rich.console import Console
console = Console()

import interface  # for printing to terminal
import memgpt.agent as agent
import memgpt.system as system
import memgpt.utils as utils
import memgpt.presets as presets
import memgpt.constants as constants
import memgpt.personas.personas as personas
import memgpt.humans.humans as humans
from memgpt.persistence_manager import InMemoryStateManager, InMemoryStateManagerWithPreloadedArchivalMemory, InMemoryStateManagerWithFaiss

import glob
def get_most_recent_json_file(name:str):
    directory_path=f"X:\AI\MemGPT\MemGPT\saved_state\{name}"
    # Construct the glob pattern to match .json files
    pattern = os.path.join(directory_path, '*-*.json')
    # Use glob to find all matching files
    json_files = glob.glob(pattern)
    if not json_files:
        return None  # No .json files found
    # Sort the list of .json files by file name (in reverse) to get the most recent one
    most_recent_json_file = max(json_files, key=os.path.basename)
    # Extract the file name from the full path
    file_name = os.path.basename(most_recent_json_file)
    return file_name

import tkinter as tk
def get_multiline_input(callback):
    def submit():
        text = text_widget.get("1.0", "end-1c")  # Retrieve text from Text widget
        callback(text)  # Pass the entered text to the callback function
        root.destroy() # Close the Tkinter window

    root = tk.Tk()
    root.title("Multi-line Text Input")

    label = tk.Label(root, text="Enter your multi-line text:")
    label.pack()

    text_widget = tk.Text(root, height=10, width=40)
    text_widget.pack()

    submit_button = tk.Button(root, text="Submit", command=submit)
    submit_button.pack()

    root.mainloop()

user_input = ''
user_input_list = []

def process_text(text):
    # Do something with the entered text
    user_input_list.append(text)

get_multiline_input(process_text)

FLAGS = flags.FLAGS
flags.DEFINE_string("persona", default=personas.DEFAULT, required=False, help="Specify persona")
flags.DEFINE_string("human", default=humans.DEFAULT, required=False, help="Specify human")
flags.DEFINE_string("model", default=constants.DEFAULT_MEMGPT_MODEL, required=False, help="Specify the LLM model")
flags.DEFINE_boolean("first", default=True, required=False, help="Use -first to send the first message in the sequence")
flags.DEFINE_boolean("debug", default=False, required=False, help="Use -debug to enable debugging output")
flags.DEFINE_boolean("no_verify", default=False, required=False, help="Bypass message verification")
flags.DEFINE_string("archival_storage_faiss_path", default="", required=False, help="Specify archival storage with FAISS index to load (a folder with a .index and .json describing documents to be loaded)")
flags.DEFINE_string("archival_storage_files", default="", required=False, help="Specify files to pre-load into archival memory (glob pattern)")
flags.DEFINE_string("archival_storage_files_compute_embeddings", default="", required=False, help="Specify files to pre-load into archival memory (glob pattern), and compute embeddings over them")
flags.DEFINE_string("archival_storage_sqldb", default="", required=False, help="Specify SQL database to pre-load into archival memory")


def clear_line():
    if os.name == 'nt':  # for windows
        console.print("\033[A\033[K", end="")
    else:  # for linux
        sys.stdout.write("\033[2K\033[G")
        sys.stdout.flush()

async def main():
    FLAGS(sys.argv)
    # print(f"persona: {FLAGS.persona}")
    # print(f"human: {FLAGS.human}")
    # print(f"model: {FLAGS.model}")
    # print(f"first: {FLAGS.first}")
    # print(f"debug: {FLAGS.debug}")
    # print(f"archival_storage_faiss_path: {FLAGS.archival_storage_faiss_path}")
    # print(f"archival_storage_files: {FLAGS.archival_storage_files}")


    utils.DEBUG = FLAGS.debug
    logging.getLogger().setLevel(logging.CRITICAL)
    if FLAGS.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    print("Running... [exit by typing '/exit']")

    if FLAGS.archival_storage_faiss_path:
        index, archival_database = utils.prepare_archival_index(FLAGS.archival_storage_faiss_path)
        persistence_manager = InMemoryStateManagerWithFaiss(index, archival_database)
    elif FLAGS.archival_storage_files:
        archival_database = utils.prepare_archival_index_from_files(FLAGS.archival_storage_files)
        print(f"Preloaded {len(archival_database)} chunks into archival memory.")
        persistence_manager = InMemoryStateManagerWithPreloadedArchivalMemory(archival_database)
    elif FLAGS.archival_storage_files_compute_embeddings:
        faiss_save_dir = await utils.prepare_archival_index_from_files_compute_embeddings(FLAGS.archival_storage_files_compute_embeddings)
        interface.important_message(f"To avoid computing embeddings next time, replace --archival_storage_files_compute_embeddings={FLAGS.archival_storage_files_compute_embeddings} with\n\t --archival_storage_faiss_path={faiss_save_dir} (if your files haven't changed).")
        index, archival_database = utils.prepare_archival_index(faiss_save_dir)
        persistence_manager = InMemoryStateManagerWithFaiss(index, archival_database)
    else:
        persistence_manager = InMemoryStateManager()
    memgpt_agent = presets.use_preset(presets.DEFAULT, FLAGS.model, personas.get_persona_text(FLAGS.persona), humans.get_human_text(FLAGS.human), interface, persistence_manager)

    profile_name = os.path.splitext(os.path.basename(FLAGS.human))[0]
    most_recent_json = get_most_recent_json_file(name=profile_name)
    if most_recent_json is not None:
        memgpt_agent.load_from_json_file_inplace(f"X:\AI\MemGPT\saved_state\{profile_name}\{most_recent_json}")
    else:
        if not os.path.exists(f"X:\AI\MemGPT\MemGPT\saved_state\{profile_name}"):
            os.makedirs(f"X:\AI\MemGPT\MemGPT\saved_state\{profile_name}")
            print(f"This is your first time on this profile.\nThere is no conversation history.\nFuture conversations will be saved under X:\AI\MemGPT\MemGPT\saved_state\{profile_name}")
        else:
            print(f"There is no conversation history in this profile.")

    print_messages = interface.print_messages
    await print_messages(memgpt_agent.messages)


    counter = 0
    global user_input
    skip_next_user_input = False
    user_message = None
    USER_GOES_FIRST = FLAGS.first

    if FLAGS.archival_storage_sqldb:
        if not os.path.exists(FLAGS.archival_storage_sqldb):
            print(f"File {FLAGS.archival_storage_sqldb} does not exist")
            return
        # Ingest data from file into archival storage
        else:
            print(f"Database found! Loading database into archival memory")
            data_list = utils.read_database_as_list(FLAGS.archival_storage_sqldb)
            user_message = f"Your archival memory has been loaded with a SQL database called {data_list[0]}, which contains schema {data_list[1]}. Remember to refer to this first while answering any user questions!"
            for row in data_list:
                await memgpt_agent.persistence_manager.archival_memory.insert(row)
            print(f"Database loaded into archival memory.")

    # auto-exit for
    if "GITHUB_ACTIONS" in os.environ:
        return

    if not USER_GOES_FIRST:
        console.input('[bold cyan]Hit enter to begin (will request first MemGPT message)[/bold cyan]')
        clear_line()
        print()

    while True:
        if not skip_next_user_input and (counter > 0 or USER_GOES_FIRST):
            # Ask for user input
            # user_input = console.input("[bold cyan]Enter your message:[/bold cyan] ")
            user_input = "\n".join(user_input_list)
            clear_line()

            if user_input.startswith('!'):
                print(f"Commands for CLI begin with '/' not '!'")
                continue

            if user_input == "":
                # no empty messages allowed
                print("Empty input received. Try again!")
                continue

            # Handle CLI commands
            # Commands to not get passed as input to MemGPT
            if user_input.startswith('/'):

                if user_input == "//":
                    print("Entering multiline mode, type // when done")
                    user_input_list = []
                    while True:
                        user_input = console.input("[bold cyan]>[/bold cyan] ")
                        clear_line()
                        if user_input == "//":
                            break
                        else:
                            user_input_list.append(user_input)

                    # pass multiline inputs to MemGPT
                    user_message = system.package_user_message("\n".join(user_input_list))

                elif user_input.lower() == "/exit":
                    break

                elif user_input.lower() == "/savechat":
                    filename = utils.get_local_time().replace(' ', '_').replace(':', '_')
                    filename = f"{filename}.pkl"
                    try:
                        if not os.path.exists("saved_chats"):
                            os.makedirs("saved_chats")
                        with open(os.path.join('saved_chats', filename), 'wb') as f:
                            pickle.dump(memgpt_agent.messages, f)
                            print(f"Saved messages to: {filename}")
                    except Exception as e:
                        print(f"Saving chat to {filename} failed with: {e}")
                    continue

                elif user_input.lower() == "/save":
                    filename = utils.get_local_time().replace(' ', '_').replace(':', '_')
                    filename = f"{filename}.json"
                    filename = os.path.join('saved_state', filename)
                    try:
                        if not os.path.exists("saved_state"):
                            os.makedirs("saved_state")
                        memgpt_agent.save_to_json_file(filename)
                        print(f"Saved checkpoint to: {filename}")
                    except Exception as e:
                        print(f"Saving state to {filename} failed with: {e}")

                    # save the persistence manager too
                    filename = filename.replace('.json', '.persistence.pickle')
                    try:
                        memgpt_agent.persistence_manager.save(filename)
                        print(f"Saved persistence manager to: {filename}")
                    except Exception as e:
                        print(f"Saving persistence manager to {filename} failed with: {e}")

                    continue

                elif user_input.lower() == "/load" or user_input.lower().startswith("/load "):
                    command = user_input.strip().split()
                    filename = command[1] if len(command) > 1 else None
                    if filename is not None:
                        if filename[-5:] != '.json':
                            filename += '.json'
                        try:
                            memgpt_agent.load_from_json_file_inplace(filename)
                            print(f"Loaded checkpoint {filename}")
                        except Exception as e:
                            print(f"Loading {filename} failed with: {e}")
                    else:
                        # Load the latest file 
                        print(f"/load warning: no checkpoint specified, loading most recent checkpoint instead")
                        json_files = glob.glob("saved_state/*.json")  # This will list all .json files in the current directory.
        
                        # Check if there are any json files.
                        if not json_files:
                            print(f"/load error: no .json checkpoint files found")
                        else:
                            # Sort files based on modified timestamp, with the latest file being the first.
                            filename = max(json_files, key=os.path.getmtime)
                            try:
                                memgpt_agent.load_from_json_file_inplace(filename)
                                print(f"Loaded checkpoint {filename}")
                            except Exception as e:
                                print(f"Loading {filename} failed with: {e}")

                    # need to load persistence manager too
                    filename = filename.replace('.json', '.persistence.pickle')
                    try:
                        memgpt_agent.persistence_manager = InMemoryStateManager.load(filename)  # TODO(fixme):for different types of persistence managers that require different load/save methods
                        print(f"Loaded persistence manager from {filename}")
                    except Exception as e:
                        print(f"/load warning: loading persistence manager from {filename} failed with: {e}")

                    continue

                elif user_input.lower() == "/dump":
                    await print_messages(memgpt_agent.messages)
                    continue

                elif user_input.lower() == "/dumpraw":
                    await interface.print_messages_raw(memgpt_agent.messages)
                    continue

                elif user_input.lower() == "/dump1":
                    await print_messages(memgpt_agent.messages[-1])
                    continue

                elif user_input.lower() == "/memory":
                    print(f"\nDumping memory contents:\n")
                    print(f"{str(memgpt_agent.memory)}")
                    print(f"{str(memgpt_agent.persistence_manager.archival_memory)}")
                    print(f"{str(memgpt_agent.persistence_manager.recall_memory)}")
                    continue

                elif user_input.lower() == "/model":
                    if memgpt_agent.model == 'gpt-4':
                        memgpt_agent.model = 'gpt-3.5-turbo'
                    elif memgpt_agent.model == 'gpt-3.5-turbo':
                        memgpt_agent.model = 'gpt-4'
                    print(f"Updated model to:\n{str(memgpt_agent.model)}")
                    continue

                elif user_input.lower() == "/pop" or user_input.lower().startswith("/pop "):
                    # Check if there's an additional argument that's an integer
                    command = user_input.strip().split()
                    amount = int(command[1]) if len(command) > 1 and command[1].isdigit() else 2
                    print(f"Popping last {amount} messages from stack")
                    memgpt_agent.messages = memgpt_agent.messages[:-amount]
                    continue

                # No skip options
                elif user_input.lower() == "/wipe":
                    memgpt_agent = agent.AgentAsync(interface)
                    user_message = None

                elif user_input.lower() == "/heartbeat":
                    user_message = system.get_heartbeat()

                elif user_input.lower() == "/memorywarning":
                    user_message = system.get_token_limit_warning()

                else:
                    print(f"Unrecognized command: {user_input}")
                    continue

            else:
                # If message did not begin with command prefix, pass inputs to MemGPT
                # Handle user message and append to messages
                user_message = system.package_user_message(user_input)

        skip_next_user_input = False

        with console.status("[bold cyan]Thinking...") as status:
            new_messages, heartbeat_request, function_failed, token_warning = await memgpt_agent.step(user_message, first_message=False, skip_verify=FLAGS.no_verify)

            # Skip user inputs if there's a memory warning, function execution failed, or the agent asked for control
            if token_warning:
                user_message = system.get_token_limit_warning()
                skip_next_user_input = True
            elif function_failed:
                user_message = system.get_heartbeat(constants.FUNC_FAILED_HEARTBEAT_MESSAGE)
                skip_next_user_input = True
            elif heartbeat_request:
                user_message = system.get_heartbeat(constants.REQ_HEARTBEAT_MESSAGE)
                skip_next_user_input = True

        counter += 1

    print("Finished.")


if __name__ ==  '__main__':

    def run(argv):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())

    app.run(run)
