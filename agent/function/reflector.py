

class Reflector:
    def __init__(self, reflector):
        self.reflector = reflector

    def reflect(self, letter):
        # TODO: allow generating the command to run the code script.
        # TODO: allow handling the issues that are not comes from the code script.
        # TODO: allow handling the program timeout.
        if task.debug:
            debug_success = False
            command = f"python {self.entry_file}"
            with self.console.status(f"Running the code script with command: {command}"):
                run_log, exit_code = run_command([command])

            if exit_code != 0:
                for attempt in range(task.debug):
                    self.console.log("Debugging the code script...")
                    self.chat_history.append(
                        {"role": 'user', "content": pmpt_chain_debug(language, self.requirement, code, run_log)})
                    code = self.handle_streaming()
                    with self.console.status(f"Running the code script..."):
                        run_log, exit_code = run_command([command])

                    if exit_code == 0:
                        debug_success = True
                        self.console.log("Debugging successful, the code script has been saved.")
                        break

                if not debug_success:
                    self.console.log(f"Debugging failed after {task.debug} attempts.")
                    return None