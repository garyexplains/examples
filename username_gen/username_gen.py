import random
import argparse
from datetime import datetime

def load_words(filename):
    """Load words from a text file, one per line"""
    with open(filename, 'r', encoding='utf-8') as f:
        # Strip whitespace and remove empty lines
        words = [line.strip() for line in f if line.strip()]
    return words

def generate_username(words1, words2, words3, words4, separator="", capitalize=False, add_number=False):
    w1 = random.choice(words1)
    w2 = random.choice(words2)
    w3 = random.choice(words3)
    w4 = random.choice(words4)
    
    if capitalize:
        # Capitalize each word (e.g. DavidSmithRunningPony)
        username = (w1.capitalize() +
                    separator + w2.capitalize() +
                    separator + w3.capitalize() +
                    separator + w4.capitalize())
    else:
        # Force everything to lowercase
        username = (w1.lower() +
                    separator + w2.lower() +
                    separator + w3.lower() +
                    separator + w4.lower())
    
    if add_number:
        # Add a random 2 or 4 digit number
        num = random.choice([random.randint(10, 99), random.randint(1000, 9999)])
        username += str(num)
    
    return username

def main():
    parser = argparse.ArgumentParser(
        description="Advanced 4-Word Username Generator"
    )
    
    parser.add_argument('-n', '--number', type=int, default=15,
                        help="Number of usernames to generate (default: 15)")
    parser.add_argument('-s', '--separator', type=str, default="",
                        choices=['', '_', '-', '.', '+'],
                        help="Separator between words (default: none)")
    parser.add_argument('-c', '--capitalize', action='store_true',
                        help="Capitalize each word (e.g. DavidSmithRunningPony)")
    parser.add_argument('--add_number', action='store_true',
                        help="Add a random number at the end")
    parser.add_argument('--files', nargs=4, 
                        default=['words1.txt', 'words2.txt', 'words3.txt', 'words4.txt'],
                        help="Paths to the four word list files")
    parser.add_argument('-o', '--output', type=str,
                        help="Save usernames to a text file")
    
    args = parser.parse_args()
    
    try:
        # Load all four lists
        list1 = load_words(args.files[0])
        list2 = load_words(args.files[1])
        list3 = load_words(args.files[2])
        list4 = load_words(args.files[3])
        
        print(f"✅ Loaded {len(list1)} words from {args.files[0]}")
        print(f"✅ Loaded {len(list2)} words from {args.files[1]}")
        print(f"✅ Loaded {len(list3)} words from {args.files[2]}")
        print(f"✅ Loaded {len(list4)} words from {args.files[3]}\n")
        
        if not all([list1, list2, list3, list4]):
            print("❌ Error: One or more word lists are empty!")
            return
        
        print(f"Generating {args.number} usernames...\n")
        print("=" * 60)
        
        usernames = []
        for i in range(args.number):
            username = generate_username(
                list1, list2, list3, list4,
                separator=args.separator,
                capitalize=args.capitalize,
                add_number=args.add_number
            )
            usernames.append(username)
            print(f"{i+1:3d}. {username}")
        
        # Save to file if requested
        if args.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = args.output if args.output.endswith('.txt') else f"{args.output}_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Username Generator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Settings: separator='{args.separator}', capitalize={args.capitalize}, "
                       f"add_number={args.add_number}\n")
                f.write("=" * 60 + "\n")
                for user in usernames:
                    f.write(user + "\n")
            
            print(f"\n✅ Usernames saved to: {filename}")
            
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()