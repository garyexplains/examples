# 4-Word Username Generator

A simple yet powerful Python script that generates unique usernames by combining random words from **four** different text files.

Perfect for creating gamer tags, usernames, account names, or creative handles.

## Features

- Combines one word from each of the four word lists
- Supports optional separator (`_`, `-`, `.`, `+`)
- Two output styles:
  - Lowercase (default) – all words forced to lowercase
  - Capitalized (`-c`) – each word starts with a capital letter
- Option to add a random 2 or 4-digit number at the end
- Clean output by default (no line numbers)
- Optional line numbers with `--linenumbers`
- Saves generated usernames to a text file
- Easy to customize word lists
- Command-line interface with helpful options

## File Structure

```
username-generator/
├── username_generator.py     # Main script
├── words1.txt                # First names
├── words2.txt                # Surnames
├── words3.txt                # Present continuous verbs (-ing)
├── words4.txt                # Objects & animals
└── README.md
```

## Word Lists Included

| File         | Content                          | Example Words                     |
|--------------|----------------------------------|-----------------------------------|
| `words1.txt` | Common first names               | david, john, ralph, michael      |
| `words2.txt` | Common surnames                  | smith, johnson, brown, garcia    |
| `words3.txt` | Present continuous verbs         | running, singing, jumping, coding|
| `words4.txt` | Common objects and animals       | pony, frog, tree, eagle, dragon  |

## Installation & Usage

1. Make sure you have Python 3 installed.
2. Place all files in the same folder.
3. Run the script using the command line.

### Basic Examples

```bash
# Generate 15 usernames (default)
python username_generator.py

# Generate 30 usernames with underscore
python username_generator.py -n 30 -s "_"

# Capitalized usernames with numbers
python username_generator.py -n 20 -c --add_number

# Lowercase with hyphen separator + save to file
python username_generator.py -n 50 -s "-" -o my_usernames
```

### All Available Options

| Option               | Description                                      | Default     |
|----------------------|--------------------------------------------------|-------------|
| `-n`, `--number`     | Number of usernames to generate                  | 15          |
| `-s`, `--separator`  | Separator between words (`_`, `-`, `.`, `+`)    | (none)      |
| `-c`, `--capitalize` | Capitalize each word                             | False       |
| `--add_number`       | Add random number at the end                     | False       |
| `--linenumbers`      | Show line numbers (1., 2., etc.) in console output | False    |
| `-o`, `--output`     | Save results to a text file                      | None        |
| `--files`            | Custom paths to the four word list files         | default     |

## Example Output

**Without `-c`:**
```
davidgarciarunningpony
johnsmithsingingeagle
ralphbrownjumpingwolf
```

**With `-c`:**
```
DavidGarciaRunningPony
JohnSmithSingingEagle
RalphBrownJumpingWolf
```

## Customization

Feel free to edit the four `.txt` files:
- One word per line
- Empty lines and comments are ignored
- You can replace them with your own themes (adjectives, fantasy words, games, brands, etc.)

## License

Free to use, modify, and distribute.

---

**Made with ❤️ for creative username generation**

Enjoy creating cool usernames!
