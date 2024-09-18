#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// Maximum lengths and sizes
#define MAX_LINE_LENGTH 1024
#define MAX_VARIABLES 100
#define MAX_FUNCTIONS 50
#define MAX_PARAMETERS 10
#define MAX_BODY_LINES 1000   // Increased to handle larger files
#define MAX_LIST_ITEMS 100

// Enum for value types
typedef enum {
    VAL_NUMBER,
    VAL_STRING,
    VAL_LIST,
    VAL_NULL
} ValueType;

// Struct for Value
typedef struct {
    ValueType type;
    double number;
    char *string;
    char **list;
    int list_size;
} Value;

// Struct for Variable
typedef struct {
    char name[50];
    Value value;
} Variable;

// Struct for Function
typedef struct {
    char name[50];
    char parameters[MAX_PARAMETERS][50];
    int param_count;
    char *body[MAX_BODY_LINES];
    int body_length;
} Function;

// Symbol tables
Variable variables[MAX_VARIABLES];
int var_count = 0;

Function functions[MAX_FUNCTIONS];
int func_count = 0;

// Function Prototypes
Value evaluate_expression(char *expr);
Value get_variable(char *name);
void set_variable(char *name, Value value);
void add_function(Function func);
Function* get_function(char *name);
void execute_block(char *lines[], int start, int end);
void trim_newline(char *str);
char* trim_whitespace(char *str);
Value parse_list(char *str);

// Function to trim leading and trailing whitespace
char* trim_whitespace(char *str) {
    // Trim leading whitespace
    while(isspace(*str)) str++;

    // If all spaces
    if(*str == 0)
        return str;

    // Trim trailing whitespace
    char *end = str + strlen(str) - 1;
    while(end > str && isspace(*end)) end--;

    // Write new null terminator
    *(end+1) = '\0';

    return str;
}

// Function to trim newline characters
void trim_newline(char *str) {
    int len = strlen(str);
    while(len > 0 && (str[len-1] == '\n' || str[len-1] == '\r')) {
        str[len-1] = '\0';
        len--;
    }
}

// Function to parse a list string into a Value
Value parse_list(char *str) {
    Value list_val;
    list_val.type = VAL_LIST;
    list_val.list_size = 0;
    list_val.list = malloc(sizeof(char*) * MAX_LIST_ITEMS);

    // Expecting format: [item1, item2, ...]
    if (str[0] == '[' && str[strlen(str)-1] == ']') {
        char items_str[512];
        strncpy(items_str, str + 1, strlen(str) - 2);
        items_str[strlen(str)-2] = '\0';

        char *item = strtok(items_str, ",");
        while (item && list_val.list_size < MAX_LIST_ITEMS) {
            list_val.list[list_val.list_size++] = strdup(trim_whitespace(item));
            item = strtok(NULL, ",");
        }
    }

    return list_val;
}

// Function to get a variable's value
Value get_variable(char *name) {
    for (int i = 0; i < var_count; i++) {
        if (strcmp(variables[i].name, name) == 0) {
            return variables[i].value;
        }
    }
    Value null_val;
    null_val.type = VAL_NULL;
    return null_val;
}

// Function to set a variable's value
void set_variable(char *name, Value value) {
    // Check if variable exists
    for (int i = 0; i < var_count; i++) {
        if (strcmp(variables[i].name, name) == 0) {
            // Free previous value if string
            if (variables[i].value.type == VAL_STRING && variables[i].value.string != NULL) {
                free(variables[i].value.string);
            }
            // Free previous list if applicable
            if (variables[i].value.type == VAL_LIST && variables[i].value.list != NULL) {
                for (int li = 0; li < variables[i].value.list_size; li++) {
                    free(variables[i].value.list[li]);
                }
                free(variables[i].value.list);
            }
            variables[i].value = value;
            return;
        }
    }
    // Add new variable
    if (var_count < MAX_VARIABLES) {
        strcpy(variables[var_count].name, name);
        variables[var_count].value = value;
        var_count++;
    }
    else {
        printf("Variable table full. Cannot add variable: %s\n", name);
    }
}

// Function to add a function to the function table
void add_function(Function func) {
    if (func_count < MAX_FUNCTIONS) {
        functions[func_count++] = func;
    }
    else {
        printf("Function table full. Cannot add function: %s\n", func.name);
    }
}

// Function to get a function by name
Function* get_function(char *name) {
    for (int i = 0; i < func_count; i++) {
        if (strcmp(functions[i].name, name) == 0) {
            return &functions[i];
        }
    }
    return NULL;
}

// Function to evaluate an expression and return a Value
Value evaluate_expression(char *expr) {
    Value result;
    memset(&result, 0, sizeof(Value));

    // Make a copy of the expression to avoid modifying the original string
    char expr_copy[512];
    strncpy(expr_copy, expr, sizeof(expr_copy) - 1);
    expr_copy[sizeof(expr_copy) - 1] = '\0'; // Ensure null-termination

    // Determine the type of operation based on operators
    int has_plus_operator = strstr(expr_copy, " plus ") != NULL;
    int has_add_operator = strchr(expr_copy, '+') != NULL;

    if (has_plus_operator) {
        // Numerical addition using 'plus'
        double sum = 0;
        int expecting_operator = 0; // Flag to check if the next token should be an operator

        char *token;
        char *saveptr;
        token = strtok_r(expr_copy, " ", &saveptr);
        while (token != NULL) {
            if (strcmp(token, "plus") == 0) {
                // Expect the next token to be an operand
                expecting_operator = 1;
            }
            else {
                // Determine if the token is a number
                int is_number = 1;
                int len = strlen(token);
                for(int i=0;i<len;i++) {
                    if(!isdigit(token[i]) && token[i] != '-' && token[i] != '.') {
                        is_number = 0;
                        break;
                    }
                }

                if(is_number) {
                    double num = atof(token);
                    if (expecting_operator) {
                        sum += num;
                        expecting_operator = 0;
                    }
                    else {
                        sum = num;
                    }
                }
                else {
                    // Assume it's a variable
                    Value var = get_variable(token);
                    if(var.type == VAL_NUMBER) {
                        if (expecting_operator) {
                            sum += var.number;
                            expecting_operator = 0;
                        }
                        else {
                            sum = var.number;
                        }
                    }
                    else {
                        printf("Unsupported type for addition or variable not found: %s\n", token);
                    }
                }
            }
            token = strtok_r(NULL, " ", &saveptr);
        }

        // Set the result
        result.type = VAL_NUMBER;
        result.number = sum;
        return result;
    }
    else if (has_add_operator) {
        // String concatenation using '+'
        // Split the expression by '+' operator
        char *tokens[50];
        int token_count = 0;
        char *token;
        char *saveptr;
        token = strtok_r(expr_copy, "+", &saveptr);
        while (token != NULL && token_count < 50) {
            tokens[token_count++] = trim_whitespace(token);
            token = strtok_r(NULL, "+", &saveptr);
        }

        // Initialize the result string
        char *concatenated = malloc(1);
        concatenated[0] = '\0';

        for(int i=0; i < token_count; i++) {
            char *current = tokens[i];
            if(current[0] == '"' || current[0] == '\'') {
                // String literal
                size_t len = strlen(current);
                if(current[len-1] == '"' || current[len-1] == '\'') {
                    current[len-1] = '\0'; // Remove trailing quote
                }
                concatenated = realloc(concatenated, strlen(concatenated) + strlen(current + 1) + 1);
                strcat(concatenated, current + 1); // Skip leading quote
            }
            else {
                // Variable or number
                // Check if it's a number
                int is_number = 1;
                int len = strlen(current);
                for(int j=0; j<len; j++) {
                    if(!isdigit(current[j]) && current[j] != '-' && current[j] != '.') {
                        is_number = 0;
                        break;
                    }
                }

                if(is_number) {
                    char num_str[50];
                    snprintf(num_str, sizeof(num_str), "%.6lf", atof(current));
                    concatenated = realloc(concatenated, strlen(concatenated) + strlen(num_str) + 1);
                    strcat(concatenated, num_str);
                }
                else {
                    // Assume it's a variable
                    Value var = get_variable(current);
                    if(var.type == VAL_STRING) {
                        concatenated = realloc(concatenated, strlen(concatenated) + strlen(var.string) + 1);
                        strcat(concatenated, var.string);
                    }
                    else if(var.type == VAL_NUMBER) {
                        char num_str[50];
                        snprintf(num_str, sizeof(num_str), "%.6lf", var.number);
                        concatenated = realloc(concatenated, strlen(concatenated) + strlen(num_str) + 1);
                        strcat(concatenated, num_str);
                    }
                    else {
                        printf("Unsupported type for concatenation or variable not found: %s\n", current);
                    }
                }
            }
        }

        // Set the result
        result.type = VAL_STRING;
        result.string = concatenated;
        return result;
    }
    else {
        // Single operand: could be a string literal, number, or variable
        char *single = trim_whitespace(expr_copy);

        if((single[0] == '"' && single[strlen(single)-1] == '"') ||
           (single[0] == '\'' && single[strlen(single)-1] == '\'')) {
            // String literal
            single[strlen(single)-1] = '\0'; // Remove trailing quote
            result.type = VAL_STRING;
            result.string = strdup(single + 1); // Remove leading quote
        }
        else {
            // Determine if it's a number
            int is_number = 1;
            int len = strlen(single);
            for(int i=0;i<len;i++) {
                if(!isdigit(single[i]) && single[i] != '-' && single[i] != '.') {
                    is_number = 0;
                    break;
                }
            }

            if(is_number) {
                result.type = VAL_NUMBER;
                result.number = atof(single);
            }
            else {
                // Assume it's a variable
                Value var = get_variable(single);
                if(var.type == VAL_NULL) {
                    printf("Variable not found: %s\n", single);
                }
                else {
                    result = var;
                }
            }
        }

        return result;
    }
}

// Function to execute a block of lines
void execute_block(char *lines[], int start, int end) {
    for (int i = start; i < end; i++) {
        char *current_line = trim_whitespace(lines[i]);
        if (strlen(current_line) == 0 || current_line[0] == '#') {
            // Empty line or comment, skip
            continue;
        }

        // Handle variable declarations: let variableName is value
        if (strncmp(current_line, "let", 3) == 0) {
            char var_name[50];
            char expr[256];
            sscanf(current_line, "let %s is %[^\n]", var_name, expr);
            Value val = evaluate_expression(expr);
            set_variable(var_name, val);
            continue;
        }

        // Handle say command: say "Message" + var + "!"
        if (strncmp(current_line, "say", 3) == 0) {
            char *expr_start = strstr(current_line, "say") + 3;
            char expr[512];
            strcpy(expr, trim_whitespace(expr_start));
            Value val = evaluate_expression(expr);
            if (val.type == VAL_NUMBER) {
                printf("%.6lf\n", val.number);
            }
            else if (val.type == VAL_STRING) {
                printf("%s\n", val.string);
            }
            else {
                printf("Unsupported type in say command.\n");
            }
            continue;
        }

        // Handle function calls: functionName with arg1 and arg2
        char func_call[50];
        if (sscanf(current_line, "%s with %[^\n]", func_call, NULL) >= 1) {
            // Find 'with' in the line
            char *with_ptr = strstr(current_line, " with ");
            if (with_ptr) {
                // Extract function name
                char func_name[50];
                strncpy(func_name, current_line, with_ptr - current_line);
                func_name[with_ptr - current_line] = '\0';
                strcpy(func_name, trim_whitespace(func_name));

                // Extract arguments
                char args_str[256];
                strcpy(args_str, with_ptr + strlen(" with "));
                // Split arguments by 'and'
                char *arg_tokens[MAX_PARAMETERS];
                int arg_count = 0;
                char *arg = strtok(args_str, " and ");
                while (arg && arg_count < MAX_PARAMETERS) {
                    arg = trim_whitespace(arg);
                    arg_tokens[arg_count++] = arg;
                    arg = strtok(NULL, " and ");
                }

                // Get function definition
                Function *func = get_function(func_name);
                if (func == NULL) {
                    printf("Function '%s' not defined.\n", func_name);
                    continue;
                }

                // Set up local variables (parameters)
                for (int p = 0; p < func->param_count && p < arg_count; p++) {
                    Value arg_val = evaluate_expression(arg_tokens[p]);
                    set_variable(func->parameters[p], arg_val);
                }

                // Execute function body
                execute_block(func->body, 0, func->body_length);
            }
            continue;
        }

        // Handle unsupported statements
        printf("Unsupported or invalid statement: %s\n", current_line);
    }
}

int main(int argc, char *argv[]) {
    // Check if a filename is provided
    if(argc != 2) {
        printf("Usage: %s <filename.el>\n", argv[0]);
        return 1;
    }

    // Open the file
    FILE *file = fopen(argv[1], "r");
    if(file == NULL) {
        perror("Error opening file");
        return 1;
    }

    // Read the file line by line
    char buffer[MAX_LINE_LENGTH];
    char *lines[MAX_BODY_LINES];
    int total_lines = 0;

    while(fgets(buffer, sizeof(buffer), file) != NULL && total_lines < MAX_BODY_LINES) {
        trim_newline(buffer);
        char *trimmed = trim_whitespace(buffer);
        // Duplicate the line and store it
        lines[total_lines++] = strdup(trimmed);
    }

    fclose(file);

    // Execute each line
    int i = 0;
    while (i < total_lines) {
        char *current_line = lines[i];
        if (strlen(current_line) == 0 || current_line[0] == '#') {
            // Empty line or comment, skip
            i++;
            continue;
        }

        // Handle function definitions
        if (strncmp(current_line, "define", 6) == 0) {
            Function func;
            memset(&func, 0, sizeof(Function));

            // Parse function name
            char func_name[50];
            sscanf(current_line, "define %s", func_name);
            // Remove any trailing characters after the name
            char *space = strchr(func_name, ' ');
            if (space) *space = '\0';
            strcpy(func.name, func_name);

            // Parse parameters
            char *params_start = strstr(current_line, "parameters [");
            if (params_start) {
                params_start += strlen("parameters [");
                char *params_end = strchr(params_start, ']');
                if (params_end) {
                    char params_str[256];
                    strncpy(params_str, params_start, params_end - params_start);
                    params_str[params_end - params_start] = '\0';

                    // Split parameters by comma
                    char *param = strtok(params_str, ",");
                    while (param && func.param_count < MAX_PARAMETERS) {
                        param = trim_whitespace(param);
                        strcpy(func.parameters[func.param_count++], param);
                        param = strtok(NULL, ",");
                    }
                }
            }

            // Read function body until 'end'
            i++; // Move to next line
            while (i < total_lines) {
                char *body_line = trim_whitespace(lines[i]);
                if (strcmp(body_line, "end") == 0) {
                    break;
                }
                func.body[func.body_length++] = strdup(body_line);
                i++;
            }

            // Add function to function table
            add_function(func);
            i++; // Skip 'end'
            continue;
        }

        // Handle for each loops
        if (strncmp(current_line, "for each", 8) == 0) {
            // Example: for each number in [1, 2, 3, 4, 5] do
            char var_name[50];
            char list_str[256];
            sscanf(current_line, "for each %s in %[^\n] do", var_name, list_str);

            // Remove 'do' from list_str
            char *do_ptr = strstr(list_str, " do");
            if (do_ptr) *do_ptr = '\0';

            // Parse the list
            Value list = parse_list(list_str);

            // Find the block of lines inside the loop
            int loop_start = i + 1;
            int loop_end = loop_start;
            int nested = 1;
            while (loop_end < total_lines && nested > 0) {
                char *loop_line = trim_whitespace(lines[loop_end]);
                if (strncmp(loop_line, "for each", 8) == 0) {
                    nested++;
                }
                else if (strcmp(loop_line, "end") == 0) {
                    nested--;
                    if (nested == 0) break;
                }
                loop_end++;
            }

            // Execute the loop for each item
            for (int j = 0; j < list.list_size; j++) {
                // Set the loop variable
                Value item;
                // Determine if the list item is a number or string
                char *current_item = list.list[j];
                if ((current_item[0] == '"' && current_item[strlen(current_item)-1] == '"') ||
                    (current_item[0] == '\'' && current_item[strlen(current_item)-1] == '\'')) {
                    // String value
                    item.type = VAL_STRING;
                    current_item[strlen(current_item)-1] = '\0'; // Remove trailing quote
                    item.string = strdup(current_item + 1); // Remove leading quote
                }
                else if (isdigit(current_item[0]) || (current_item[0] == '-' && isdigit(current_item[1]))) {
                    // Number value
                    item.type = VAL_NUMBER;
                    item.number = atof(current_item);
                }
                else {
                    // Assume variable
                    item = get_variable(current_item);
                }
                set_variable(var_name, item);

                // Execute the loop body
                execute_block(lines, loop_start, loop_end);
            }
            i = loop_end + 1;
            continue;
        }

        // Handle variable declarations: let variableName is value
        if (strncmp(current_line, "let", 3) == 0) {
            char var_name[50];
            char expr[256];
            sscanf(current_line, "let %s is %[^\n]", var_name, expr);
            Value val = evaluate_expression(expr);
            set_variable(var_name, val);
            i++;
            continue;
        }

        // Handle ask command: ask "Question" and store in variable
        if (strncmp(current_line, "ask", 3) == 0) {
            char question[256];
            char var_name[50];
            sscanf(current_line, "ask \"%[^\"]\" and store in %s", question, var_name);
            printf("%s ", question);
            char input[256];
            if (fgets(input, sizeof(input), stdin) != NULL) {
                trim_newline(input);
                Value val;
                val.type = VAL_STRING;
                val.string = strdup(input);
                set_variable(var_name, val);
            }
            i++;
            continue;
        }

        // Handle say command: say "Message" + var + "!"
        if (strncmp(current_line, "say", 3) == 0) {
            char *expr_start = strstr(current_line, "say") + 3;
            char expr[512];
            strcpy(expr, trim_whitespace(expr_start));
            Value val = evaluate_expression(expr);
            if (val.type == VAL_NUMBER) {
                printf("%.6lf\n", val.number);
            }
            else if (val.type == VAL_STRING) {
                printf("%s\n", val.string);
            }
            else {
                printf("Unsupported type in say command.\n");
            }
            i++;
            continue;
        }

        // Handle function calls: functionName with arg1 and arg2
        char func_call[50];
        if (sscanf(current_line, "%s with %[^\n]", func_call, NULL) >= 1) {
            // Find 'with' in the line
            char *with_ptr = strstr(current_line, " with ");
            if (with_ptr) {
                // Extract function name
                char func_name[50];
                strncpy(func_name, current_line, with_ptr - current_line);
                func_name[with_ptr - current_line] = '\0';
                strcpy(func_name, trim_whitespace(func_name));

                // Extract arguments
                char args_str[256];
                strcpy(args_str, with_ptr + strlen(" with "));
                // Split arguments by 'and'
                char *arg_tokens[MAX_PARAMETERS];
                int arg_count = 0;
                char *arg = strtok(args_str, " and ");
                while (arg && arg_count < MAX_PARAMETERS) {
                    arg = trim_whitespace(arg);
                    arg_tokens[arg_count++] = arg;
                    arg = strtok(NULL, " and ");
                }

                // Get function definition
                Function *func = get_function(func_name);
                if (func == NULL) {
                    printf("Function '%s' not defined.\n", func_name);
                    i++;
                    continue;
                }

                // Set up local variables (parameters)
                for (int p = 0; p < func->param_count && p < arg_count; p++) {
                    Value arg_val = evaluate_expression(arg_tokens[p]);
                    set_variable(func->parameters[p], arg_val);
                }

                // Execute function body
                execute_block(func->body, 0, func->body_length);
                
                // Increment the loop variable to move to the next line
                i++;
                continue;
            }
            // If 'with' not found, still handle as unsupported
            printf("Unsupported or invalid function call: %s\n", current_line);
            i++;
            continue;
        }

        // Handle unsupported statements
        printf("Unsupported or invalid statement: %s\n", current_line);
        i++;
    }

    // Cleanup: Free all allocated memory
    for(int i = 0; i < total_lines; i++) {
        free(lines[i]);
    }

    // Free variables' allocated memory
    for(int i = 0; i < var_count; i++) {
        if(variables[i].value.type == VAL_STRING && variables[i].value.string != NULL) {
            free(variables[i].value.string);
        }
        if(variables[i].value.type == VAL_LIST && variables[i].value.list != NULL) {
            for(int j = 0; j < variables[i].value.list_size; j++) {
                free(variables[i].value.list[j]);
            }
            free(variables[i].value.list);
        }
    }

    // Free functions' allocated memory
    for(int i = 0; i < func_count; i++) {
        for(int j = 0; j < functions[i].body_length; j++) {
            free(functions[i].body[j]);
        }
    }

    return 0;
}
