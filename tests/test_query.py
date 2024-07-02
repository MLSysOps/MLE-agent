from mle.agents import CodeAgent
from mle.model import load_model

if __name__ == '__main__':
    model = CodeAgent(load_model('/Users/huangyz0918/desktop/test', 'gpt-4o'))
    print(model.handle_query('Write a Python program to calculate the factorial of a number.'))
