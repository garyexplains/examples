def evaluate_postfix(expression):
    stack = []

    for token in expression.split():
        if token.isdigit():
            print("Push on stack:", token)
            stack.append(int(token))
        else:
            b = stack.pop()
            a = stack.pop()
            if token == '+':
                print("Add and push result on stack:", a, b)
                stack.append(a + b)
            elif token == '-':
                print("Subtract and push result on stack:", a, b)
                stack.append(a - b)
            elif token == '*':
                print("Multiply and push result on stack:", a, b)
                stack.append(a * b)
            elif token == '/':
                print("Divide and push result on stack:", a, b)
                stack.append(a / b)
            elif token == '^':
                print("Raise to power and push result on stack:", a, b)
                stack.append(pow(a, b))
        print("Stack:", stack)

    return stack.pop()


postfix_expression = input("Enter a postfix expression: ")
result = evaluate_postfix(postfix_expression)
print("Result:", result)
