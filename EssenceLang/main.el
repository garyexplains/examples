# Greet the user
ask "What is your name?" and store in userName
say "Hello " + userName + "!"

# Count from 1 to 5
let count is 1
for each number in [1, 2, 3, 4, 5] do
    say "Count is " + number
end

# Define a function to add two numbers
define add with parameters [a, b] do
    let result is a plus b
    say "The sum is " + result
end

# Use the function
add with 5 and 7

# Additional Test Cases
let x is 7 plus 11
say x

say "Goodbye " + userName
