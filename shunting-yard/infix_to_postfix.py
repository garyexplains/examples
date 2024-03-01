def get_precedence(op):
    precedences = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
    return precedences.get(op, 0)

def infix_to_postfix(expression):
    output = []
    stack = []
    tokens = expression.split()

    for token in tokens:
        print("Token:", token)
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
        print("Output stack:", output)
        print("Operator stack:", stack)

    while stack:
        output.append(stack.pop())

    return ' '.join(output)


infix_expression = input("Enter an infix expression: ")
postfix_expression = infix_to_postfix(infix_expression)
print("Postfix expression:", postfix_expression)
