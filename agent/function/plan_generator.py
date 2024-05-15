import os
import yaml
from openai import OpenAI

from agent.templates import load_yml


def generate_plan(user_requirement, task_pool_yml):
    task_pool = load_yml(task_pool_yml)

    prompt = (f"User requirement: {user_requirement}\n"
              f"\nTask pool:\n{yaml.dump(task_pool)}\n"
              f"\nGenerate a project plan in the format: Task 1: ..., Task 2: ..., etc.")

    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content":"You are an assistant that helps generate machine learning project plans. "
                                         "By following that plan, LLM can help to generate code for the project."},
            {"role": "user", "content": prompt}
        ]
    )

    plan = response.choices[0].message.content

    with open('project_plan.yml', 'w') as file:
        file.write(plan)

    print("Generated Project Plan:")
    print(plan)


# Example usage

if __name__ == '__main__':
    user_requirement = "I need a project plan for developing a machine learning model to predict sentiment analysis."
    task_pool_path = 'task_pool.yml'

    generate_plan(user_requirement, task_pool_path)