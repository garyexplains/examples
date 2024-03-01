import re
import sys

def get_precedence(op):
    precedences = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
    return precedences.get(op, 0)

def infix_to_postfix(expression):
    output = []
    stack = []
    tokens = tokenize(expression)

    for token in tokens:
        if token.isnumeric():
            output.append(token)
        elif token == '(':
            stack.append(token)
        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()  # Pop the left parenthesis
        else:
            while stack and get_precedence(stack[-1]) >= get_precedence(token):
                output.append(stack.pop())
            stack.append(token)

    while stack:
        output.append(stack.pop())

    return output

def tokenize(expression):
    # Regular expression pattern for numbers and operators
    token_pattern = r'\d+|\+|-|\*|/|\(|\)|\^'
    tokens = re.findall(token_pattern, expression)
    return tokens

def evaluate_postfix(expression):
    stack = []

    for token in expression:
        if token.isdigit():
            stack.append(int(token))
        else:
            b = stack.pop()
            a = stack.pop()
            if token == '+':
                stack.append(a + b)
            elif token == '-':
                stack.append(a - b)
            elif token == '*':
                stack.append(a * b)
            elif token == '/':
                stack.append(a / b)
            elif token == '^':
                stack.append(pow(a, b))

    return stack.pop()

while True:
    if len(sys.argv) != 2:
        infix_expression = input("")
    else:
        infix_expression = sys.argv[1]

    postfix_expression = infix_to_postfix(infix_expression)
    result = evaluate_postfix(postfix_expression)
    print(result)
    if len(sys.argv) == 2:
        exit(result)