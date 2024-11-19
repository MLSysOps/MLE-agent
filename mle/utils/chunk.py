# Source modified from https://github.com/CintraAI/code-chunker/blob/main/Chunker.py
import tiktoken
from .parser import CodeParser
from abc import ABC, abstractmethod


def count_tokens(string: str, encoding_name: str) -> int:
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


class Chunker(ABC):
    def __init__(self, encoding_name="gpt-4"):
        self.encoding_name = encoding_name

    @abstractmethod
    def chunk(self, content, token_limit):
        pass

    @abstractmethod
    def get_chunk(self, chunked_content, chunk_number):
        pass

    @staticmethod
    def print_chunks(chunks):
        for chunk_number, chunk_code in chunks.items():
            print(f"Chunk {chunk_number}:")
            print("=" * 40)
            print(chunk_code)
            print("=" * 40)

    @staticmethod
    def consolidate_chunks_into_file(chunks):
        return "\n".join(chunks.values())

    @staticmethod
    def count_lines(consolidated_chunks):
        lines = consolidated_chunks.split("\n")
        return len(lines)


class CodeChunker(Chunker):
    def __init__(self, cache_dir, file_extension, encoding_name="gpt-4o-mini"):
        super().__init__(encoding_name)
        self.file_extension = file_extension
        self.cache_dir = cache_dir

    def chunk(self, code, token_limit) -> dict:
        code_parser = CodeParser(self.cache_dir, self.file_extension)
        chunks = {}
        token_count = 0
        lines = code.split("\n")
        i = 0
        chunk_number = 1
        start_line = 0
        breakpoints = sorted(code_parser.get_lines_for_points_of_interest(code, self.file_extension))
        comments = sorted(code_parser.get_lines_for_comments(code, self.file_extension))
        adjusted_breakpoints = []
        for bp in breakpoints:
            current_line = bp - 1
            highest_comment_line = None  # Initialize with None to indicate no comment line has been found yet
            while current_line in comments:
                highest_comment_line = current_line  # Update highest comment line found
                current_line -= 1  # Move to the previous line

            if highest_comment_line:  # If a highest comment line exists, add it
                adjusted_breakpoints.append(highest_comment_line)
            else:
                adjusted_breakpoints.append(
                    bp)  # If no comments were found before the breakpoint, add the original breakpoint

        breakpoints = sorted(set(adjusted_breakpoints))  # Ensure breakpoints are unique and sorted

        while i < len(lines):
            line = lines[i]
            new_token_count = count_tokens(line, self.encoding_name)
            if token_count + new_token_count > token_limit:

                # Set the stop line to the last breakpoint before the current line
                if i in breakpoints:
                    stop_line = i
                else:
                    stop_line = max(max([x for x in breakpoints if x < i], default=start_line), start_line)

                # If the stop line is the same as the start line, it means we haven't reached a breakpoint yet, and we need to move to the next line to find one
                if stop_line == start_line and i not in breakpoints:
                    token_count += new_token_count
                    i += 1

                # If the stop line is the same as the start line and the current line is a breakpoint, it means we can create a chunk with just the current line
                elif stop_line == start_line and i == stop_line:
                    token_count += new_token_count
                    i += 1

                # If the stop line is the same as the start line and the current line is a breakpoint, it means we can create a chunk with just the current line
                elif stop_line == start_line and i in breakpoints:
                    current_chunk = "\n".join(lines[start_line:stop_line])
                    if current_chunk.strip():  # If the current chunk is not just whitespace
                        chunks[chunk_number] = current_chunk  # Using chunk_number as key
                        chunk_number += 1

                    token_count = 0
                    start_line = i
                    i += 1

                # If the stop line is different from the start line, it means we're at the end of a block
                else:
                    current_chunk = "\n".join(lines[start_line:stop_line])
                    if current_chunk.strip():
                        chunks[chunk_number] = current_chunk  # Using chunk_number as key
                        chunk_number += 1

                    i = stop_line
                    token_count = 0
                    start_line = stop_line
            else:
                # If the token count is still within the limit, add the line to the current chunk
                token_count += new_token_count
                i += 1

        # Append remaining code, if any, ensuring it's not empty or whitespace
        current_chunk_code = "\n".join(lines[start_line:])
        if current_chunk_code.strip():  # Checks if the chunk is not just whitespace
            chunks[chunk_number] = current_chunk_code  # Using chunk_number as key

        return chunks

    def get_chunk(self, chunked_codebase, chunk_number):
        return chunked_codebase[chunk_number]
