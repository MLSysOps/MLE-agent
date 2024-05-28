

class Reflector:
    def __init__(self, reflector):
        self.reflector = reflector

    def pmpt_chain_debug(lang: str, requirement: str, code: str, error_log: str) -> str:
        return f"""
        You are an Machine learning engineer, and you are debugging a {lang} script with the source code and the error logs.
        Please make sure the modified code meets the task requirements and can run successfully.

        - User Requirement: {requirement}
        - Existing Code: {code}
        - Error Log: {error_log}

        The output format should be:

        Code: {{code}}
        """
    

    def reflect(self, letter):
        # TODO: after code generation
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