This project is a script interpreter for a simple language called `nuscripy`.

It is typeless. There are no `{}` and no semicolons.

The `end` keyword is used to delimit blocks, such as `if ... end` and `while ... end`.

Here is an example script that defines the major parts of the language:

```txt
// Start of example program

// Variable assignment and math
// Typeless: numbers and strings just work.
total = 0
count = 1
message = "The result is: "

// Function definition
// No types, no braces, uses 'end' to close the block.
fn calculate_bonus(val)
  multiplier = 2  // Local scope: multiplier only exists here
  if val > 10
    multiplier = 5
  end
  return val * multiplier
end

// First-class functions
// Assigning a function to a variable
operation = calculate_bonus

// Control flow: while loop
// C-style operators: <=, ++, ==
while count <= 5
  bonus = operation(count)
  total = total + bonus

  print("Current count: " + count)
  count++
end

// Final output
if total == 30
  print(message + "Perfect")
else
  print(message + total)
end

// End of example program
```

Note that `print()` is a built-in function in a standard library. The interpreter needs to be easy to extend by adding more built-in functions to the standard library of `nuscripy`.

The interpreter will be built in C. It needs a tokenizer and it needs to use an AST.

Break the project down into smaller tasks. Ask questions if needed.
