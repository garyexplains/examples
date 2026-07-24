/* stringtool: a string-manipulation CLI designed to be called by LLMs
 * that use OpenAI-style function/tool calling.
 *
 * Usage:
 *   stringtool schema            Print OpenAI-style tool schemas as JSON.
 *   stringtool <op> <json-args>  Execute one operation; print JSON result.
 *
 * The arguments and the result are both JSON objects. A thin host (Python,
 * Node, Go, etc.) reads `stringtool schema`, registers the tools with its
 * chat client, and shells out to `stringtool <op> '<json>'` whenever the
 * model invokes one.
 *
 * No external dependencies; JSON parsing/serialization is minimal but
 * sufficient for the flat objects used here.
 */

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <io.h>
#else
#include <unistd.h>
#endif

/* ----- tiny dynamic string ---------------------------------------------- */

typedef struct {
    char  *data;
    size_t len;
    size_t cap;
} sbuf;

static void sbuf_init(sbuf *s) { s->data = NULL; s->len = s->cap = 0; }

static void sbuf_reserve(sbuf *s, size_t extra) {
    if (s->len + extra + 1 <= s->cap) return;
    size_t ncap = s->cap ? s->cap * 2 : 16;
    while (s->len + extra + 1 > ncap) ncap *= 2;
    s->data = realloc(s->data, ncap);
    if (!s->data) { fprintf(stderr, "oom\n"); exit(1); }
    s->cap = ncap;
}

static void sbuf_putc(sbuf *s, char c) {
    sbuf_reserve(s, 1);
    s->data[s->len++] = c;
    s->data[s->len] = '\0';
}

static void sbuf_puts(sbuf *s, const char *str) {
    size_t n = strlen(str);
    sbuf_reserve(s, n);
    memcpy(s->data + s->len, str, n);
    s->len += n;
    s->data[s->len] = '\0';
}

static void sbuf_free(sbuf *s) { free(s->data); s->data = NULL; s->len = s->cap = 0; }

/* ----- minimal JSON value model ----------------------------------------- */
/* Supports only what we need: string, number, array (of strings), object.   */

typedef enum { J_NULL, J_STR, J_NUM, J_ARR, J_OBJ } jkind;

typedef struct jval jval;
struct jval {
    jkind  kind;
    char  *str;       /* J_STR (decoded) or J_OBJ key (when in array of pairs) */
    double num;       /* J_NUM */
    jval  *items;     /* J_ARR items or J_OBJ pairs (each pair: items[i]=key,
                         items[i+1]=value) */
    size_t count;     /* element count for arrays; pair count for objects */
};

typedef struct {
    const char *p;
    const char *start;
    const char *end;
    int         ok;
    char        err[64];
} jparser;

static void jerr(jparser *jp, const char *msg) {
    if (!jp->ok) return;
    jp->ok = 0;
    snprintf(jp->err, sizeof jp->err, "%s at offset %ld",
             msg, (long)(jp->p - jp->start));
}

static void jskipws(jparser *jp) {
    while (jp->p < jp->end && isspace((unsigned char)*jp->p)) jp->p++;
}

static jval jparse_value(jparser *jp);

static jval jval_new(jkind k) {
    jval v;
    v.kind = k; v.str = NULL; v.num = 0; v.items = NULL; v.count = 0;
    return v;
}

static void jval_free(jval *v) {
    if (!v) return;
    if (v->kind == J_OBJ) {
        for (size_t i = 0; i < v->count; i++) {
            free(v->items[2 * i].str);
            jval_free(&v->items[2 * i + 1]);
        }
    } else if (v->kind == J_ARR) {
        for (size_t i = 0; i < v->count; i++) jval_free(&v->items[i]);
    } else if (v->kind == J_STR) {
        free(v->str);
    }
    free(v->items);
    v->items = NULL;
}

static void scan_string(jparser *jp, sbuf *out) {
    if (jp->p >= jp->end || *jp->p != '"') { jerr(jp, "expected '\"'"); return; }
    jp->p++;
    while (jp->p < jp->end) {
        char c = *jp->p++;
        if (c == '"') return;
        if (c == '\\') {
            if (jp->p >= jp->end) { jerr(jp, "bad escape"); return; }
            char e = *jp->p++;
            switch (e) {
                case '"':  sbuf_putc(out, '"');  break;
                case '\\': sbuf_putc(out, '\\'); break;
                case '/':  sbuf_putc(out, '/');  break;
                case 'b':  sbuf_putc(out, '\b'); break;
                case 'f':  sbuf_putc(out, '\f'); break;
                case 'n':  sbuf_putc(out, '\n'); break;
                case 'r':  sbuf_putc(out, '\r'); break;
                case 't':  sbuf_putc(out, '\t'); break;
                case 'u': {
                    if (jp->end - jp->p < 4) { jerr(jp, "short \\u"); return; }
                    char hex[5] = {0};
                    memcpy(hex, jp->p, 4); jp->p += 4;
                    unsigned cp = (unsigned)strtoul(hex, NULL, 16);
                    if (cp < 0x80) {
                        sbuf_putc(out, (char)cp);
                    } else if (cp < 0x800) {
                        sbuf_putc(out, (char)(0xC0 | (cp >> 6)));
                        sbuf_putc(out, (char)(0x80 | (cp & 0x3F)));
                    } else {
                        sbuf_putc(out, (char)(0xE0 | (cp >> 12)));
                        sbuf_putc(out, (char)(0x80 | ((cp >> 6) & 0x3F)));
                        sbuf_putc(out, (char)(0x80 | (cp & 0x3F)));
                    }
                    break;
                }
                default: jerr(jp, "unknown escape"); return;
            }
        } else {
            sbuf_putc(out, c);
        }
    }
    jerr(jp, "unterminated string");
}

static jval jparse_string(jparser *jp) {
    jval v = jval_new(J_STR);
    sbuf s; sbuf_init(&s);
    scan_string(jp, &s);
    if (!jp->ok) { sbuf_free(&s); return v; }
    if (!s.data) { s.data = strdup(""); }
    v.str = s.data;
    return v;
}

static jval jparse_number(jparser *jp) {
    jval v = jval_new(J_NUM);
    char *endp;
    v.num = strtod(jp->p, &endp);
    if (endp == jp->p) { jerr(jp, "bad number"); return v; }
    jp->p = endp;
    return v;
}

static jval jparse_array(jparser *jp) {
    jval v = jval_new(J_ARR);
    if (*jp->p != '[') { jerr(jp, "expected '['"); return v; }
    jp->p++;
    size_t cap = 0;
    for (;;) {
        jskipws(jp);
        if (jp->p < jp->end && *jp->p == ']') { jp->p++; break; }
        jval elem = jparse_value(jp);
        if (!jp->ok) { jval_free(&elem); goto fail; }
        if (v.count >= cap) { cap = cap ? cap * 2 : 4; v.items = realloc(v.items, cap * sizeof(jval)); }
        v.items[v.count++] = elem;
        jskipws(jp);
        if (jp->p >= jp->end) { jerr(jp, "unterminated array"); goto fail; }
        if (*jp->p == ',') { jp->p++; continue; }
        if (*jp->p == ']') { jp->p++; break; }
        jerr(jp, "expected ',' or ']'"); goto fail;
    }
    return v;
fail:
    return v;
}

static jval jparse_object(jparser *jp) {
    jval v = jval_new(J_OBJ);
    if (*jp->p != '{') { jerr(jp, "expected '{'"); return v; }
    jp->p++;
    size_t cap = 0;
    for (;;) {
        jskipws(jp);
        if (jp->p < jp->end && *jp->p == '}') { jp->p++; break; }
        sbuf key; sbuf_init(&key);
        scan_string(jp, &key);
        if (!jp->ok) { sbuf_free(&key); goto fail; }
        if (!key.data) key.data = strdup("");
        jskipws(jp);
        if (jp->p >= jp->end || *jp->p != ':') { jerr(jp, "expected ':'"); sbuf_free(&key); goto fail; }
        jp->p++;
        jskipws(jp);
        jval val = jparse_value(jp);
        if (!jp->ok) { free(key.data); jval_free(&val); goto fail; }
        if (v.count >= cap) {
            cap = cap ? cap * 2 : 4;
            v.items = realloc(v.items, cap * 2 * sizeof(jval));
        }
        jval kslot = jval_new(J_STR); kslot.str = key.data;
        v.items[2 * v.count] = kslot;
        v.items[2 * v.count + 1] = val;
        v.count++;
        jskipws(jp);
        if (jp->p >= jp->end) { jerr(jp, "unterminated object"); goto fail; }
        if (*jp->p == ',') { jp->p++; continue; }
        if (*jp->p == '}') { jp->p++; break; }
        jerr(jp, "expected ',' or '}'"); goto fail;
    }
    return v;
fail:
    return v;
}

static jval jparse_value(jparser *jp) {
    jskipws(jp);
    if (jp->p >= jp->end) { jerr(jp, "empty"); return jval_new(J_NULL); }
    char c = *jp->p;
    if (c == '"')  return jparse_string(jp);
    if (c == '[')  return jparse_array(jp);
    if (c == '{')  return jparse_object(jp);
    if (c == '-' || (c >= '0' && c <= '9')) return jparse_number(jp);
    if (strncmp(jp->p, "true", 4) == 0 && jp->p + 4 <= jp->end) {
        jp->p += 4; jval v = jval_new(J_NUM); v.num = 1; return v;
    }
    if (strncmp(jp->p, "false", 5) == 0 && jp->p + 5 <= jp->end) {
        jp->p += 5; jval v = jval_new(J_NUM); v.num = 0; return v;
    }
    if (strncmp(jp->p, "null", 4) == 0 && jp->p + 4 <= jp->end) {
        jp->p += 4; return jval_new(J_NULL);
    }
    jerr(jp, "unexpected token");
    return jval_new(J_NULL);
}

static jval jparse(const char *src) {
    jparser jp;
    jp.p = src; jp.start = src; jp.end = src + strlen(src); jp.ok = 1; jp.err[0] = '\0';
    jval v = jparse_value(&jp);
    if (!jp.ok) {
        fprintf(stderr, "JSON parse error: %s\n", jp.err);
        jval_free(&v);
        exit(2);
    }
    return v;
}

static const jval *jobj_get(const jval *o, const char *key) {
    if (o->kind != J_OBJ) return NULL;
    for (size_t i = 0; i < o->count; i++) {
        if (strcmp(o->items[2 * i].str, key) == 0) return &o->items[2 * i + 1];
    }
    return NULL;
}

static const char *jstr_of(const jval *o, const char *key) {
    const jval *v = jobj_get(o, key);
    return (v && v->kind == J_STR) ? v->str : NULL;
}

static const char *jstr_of_req(const jval *o, const char *key) {
    const char *s = jstr_of(o, key);
    if (!s) { fprintf(stderr, "missing/invalid required string '%s'\n", key); exit(2); }
    return s;
}

static int jint_of(const jval *o, const char *key, int dflt) {
    const jval *v = jobj_get(o, key);
    return (v && v->kind == J_NUM) ? (int)v->num : dflt;
}

/* ----- JSON serialization of results ----------------------------------- */

static void json_escape(sbuf *out, const char *s) {
    sbuf_putc(out, '"');
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
        switch (*p) {
            case '"':  sbuf_puts(out, "\\\""); break;
            case '\\': sbuf_puts(out, "\\\\"); break;
            case '\b': sbuf_puts(out, "\\b");  break;
            case '\f': sbuf_puts(out, "\\f");  break;
            case '\n': sbuf_puts(out, "\\n");  break;
            case '\r': sbuf_puts(out, "\\r");  break;
            case '\t': sbuf_puts(out, "\\t");  break;
            default:
                if (*p < 0x20) { char b[8]; snprintf(b, sizeof b, "\\u%04x", *p); sbuf_puts(out, b); }
                else           sbuf_putc(out, (char)*p);
        }
    }
    sbuf_putc(out, '"');
}

static void jval_emit(sbuf *out, const jval *v);

static void jval_emit(sbuf *out, const jval *v) {
    switch (v->kind) {
        case J_NULL: sbuf_puts(out, "null"); break;
        case J_STR:  json_escape(out, v->str); break;
        case J_NUM: {
            char b[64];
            double i;
            if (v->num == (double)(long long)v->num) snprintf(b, sizeof b, "%lld", (long long)v->num);
            else                                     snprintf(b, sizeof b, "%.17g", v->num);
            (void)i;
            sbuf_puts(out, b);
            break;
        }
        case J_ARR:
            sbuf_putc(out, '[');
            for (size_t i = 0; i < v->count; i++) {
                if (i) sbuf_putc(out, ',');
                jval_emit(out, &v->items[i]);
            }
            sbuf_putc(out, ']');
            break;
        case J_OBJ:
            sbuf_putc(out, '{');
            for (size_t i = 0; i < v->count; i++) {
                if (i) sbuf_putc(out, ',');
                json_escape(out, v->items[2 * i].str);
                sbuf_putc(out, ':');
                jval_emit(out, &v->items[2 * i + 1]);
            }
            sbuf_putc(out, '}');
            break;
    }
}

/* Build a result object with one string field, e.g. {"result":"..."} */
static jval result_str(const char *value) {
    jval v = jval_new(J_OBJ); v.count = 1; v.items = calloc(2, sizeof(jval));
    jval k = jval_new(J_STR); k.str = strdup("result");
    jval val = jval_new(J_STR); val.str = strdup(value ? value : "");
    v.items[0] = k; v.items[1] = val;
    return v;
}

static jval result_num(double n) {
    jval v = jval_new(J_OBJ); v.count = 1; v.items = calloc(2, sizeof(jval));
    jval k = jval_new(J_STR); k.str = strdup("result");
    jval val = jval_new(J_NUM); val.num = n;
    v.items[0] = k; v.items[1] = val;
    return v;
}

static jval result_bool(int b) {
    return result_num(b ? 1 : 0);
}

static jval result_arr(size_t n) {
    jval v = jval_new(J_OBJ); v.count = 1; v.items = calloc(2, sizeof(jval));
    jval k = jval_new(J_STR); k.str = strdup("result");
    jval arr = jval_new(J_ARR); arr.count = 0; arr.items = n ? calloc(n, sizeof(jval)) : NULL;
    v.items[0] = k; v.items[1] = arr;
    return v;
}

/* ----- operations ------------------------------------------------------- */

static char *str_dup(const char *s) { char *p = malloc(strlen(s) + 1); strcpy(p, s); return p; }

static jval op_upper(const jval *args) {
    const char *s = jstr_of_req(args, "s");
    char *r = str_dup(s);
    for (char *p = r; *p; p++) *p = (char)toupper((unsigned char)*p);
    jval v = result_str(r); free(r); return v;
}
static jval op_lower(const jval *args) {
    const char *s = jstr_of_req(args, "s");
    char *r = str_dup(s);
    for (char *p = r; *p; p++) *p = (char)tolower((unsigned char)*p);
    jval v = result_str(r); free(r); return v;
}
static jval op_trim(const jval *args) {
    const char *s = jstr_of_req(args, "s");
    const char *e = s + strlen(s);
    while (s < e && isspace((unsigned char)*s)) s++;
    while (e > s && isspace((unsigned char)e[-1])) e--;
    size_t n = (size_t)(e - s);
    char *r = malloc(n + 1); memcpy(r, s, n); r[n] = '\0';
    jval v = result_str(r); free(r); return v;
}
static jval op_length(const jval *args) {
    const char *s = jstr_of_req(args, "s");
    return result_num((double)strlen(s));
}
static jval op_reverse(const jval *args) {
    const char *s = jstr_of_req(args, "s");
    size_t n = strlen(s);
    char *r = malloc(n + 1);
    for (size_t i = 0; i < n; i++) r[i] = s[n - 1 - i];
    r[n] = '\0';
    jval v = result_str(r); free(r); return v;
}
static jval op_substring(const jval *args) {
    const char *s = jstr_of_req(args, "s");
    int start = jint_of(args, "start", 0);
    int len   = jint_of(args, "length", -1);
    int n = (int)strlen(s);
    if (start < 0) start += n;
    if (start < 0) start = 0;
    if (start > n) start = n;
    int rem = n - start;
    int take = (len < 0 || len > rem) ? rem : len;
    char *r = malloc((size_t)take + 1);
    memcpy(r, s + start, (size_t)take);
    r[take] = '\0';
    jval v = result_str(r); free(r); return v;
}
static jval op_contains(const jval *args) {
    const char *s = jstr_of_req(args, "s");
    const char *sub = jstr_of_req(args, "substring");
    return result_bool(strstr(s, sub) != NULL);
}
static jval op_replace(const jval *args) {
    const char *s   = jstr_of_req(args, "s");
    const char *old = jstr_of_req(args, "old");
    const char *nu  = jstr_of_req(args, "new");
    if (!*old) { return result_str(s); }
    sbuf out; sbuf_init(&out);
    size_t oldlen = strlen(old);
    for (const char *p = s; *p; ) {
        if (strncmp(p, old, oldlen) == 0) { sbuf_puts(&out, nu); p += oldlen; }
        else sbuf_putc(&out, *p++);
    }
    if (!out.data) { out.data = str_dup(""); }
    jval v = result_str(out.data);
    sbuf_free(&out);
    return v;
}
static jval op_split(const jval *args) {
    const char *s   = jstr_of_req(args, "s");
    const char *sep = jstr_of_req(args, "separator");
    size_t seplen = strlen(sep);
    jval v = result_arr(0);
    if (seplen == 0) {
        /* split into characters */
        for (const char *p = s; *p; ++p) {
            char b[2] = { *p, 0 };
            jval e = jval_new(J_STR); e.str = str_dup(b);
            v.items[1].items = realloc(v.items[1].items, (v.items[1].count + 1) * sizeof(jval));
            v.items[1].items[v.items[1].count++] = e;
        }
        return v;
    }
    const char *p = s;
    for (;;) {
        const char *m = strstr(p, sep);
        size_t plen = m ? (size_t)(m - p) : strlen(p);
        char *part = malloc(plen + 1); memcpy(part, p, plen); part[plen] = '\0';
        jval e = jval_new(J_STR); e.str = part;
        v.items[1].items = realloc(v.items[1].items, (v.items[1].count + 1) * sizeof(jval));
        v.items[1].items[v.items[1].count++] = e;
        if (!m) break;
        p = m + seplen;
    }
    return v;
}
static jval op_join(const jval *args) {
    const char *sep = jstr_of_req(args, "separator");
    const jval *arr = jobj_get(args, "parts");
    if (!arr || arr->kind != J_ARR) {
        fprintf(stderr, "missing/invalid 'parts' array\n"); exit(2);
    }
    sbuf out; sbuf_init(&out);
    for (size_t i = 0; i < arr->count; i++) {
        if (i) sbuf_puts(&out, sep);
        if (arr->items[i].kind == J_STR) sbuf_puts(&out, arr->items[i].str);
    }
    if (!out.data) out.data = str_dup("");
    jval v = result_str(out.data);
    sbuf_free(&out);
    return v;
}

/* ----- schema (OpenAI tool format) ------------------------------------- */

typedef jval (*op_fn)(const jval *);
typedef struct { const char *name; const char *desc; op_fn fn; } op_def;

static op_def OPS[] = {
    {"upper",     "Convert all characters in s to upper case.",                 op_upper},
    {"lower",     "Convert all characters in s to lower case.",                 op_lower},
    {"trim",      "Remove leading and trailing whitespace from s.",             op_trim},
    {"length",    "Return the number of characters in s.",                      op_length},
    {"reverse",   "Reverse the characters in s.",                              op_reverse},
    {"substring", "Return substring of s starting at 'start' (0-based, \"length\" chars).", op_substring},
    {"contains",  "Return true if s contains substring.",                       op_contains},
    {"replace",   "Replace every occurrence of \"old\" with \"new\" in s.",     op_replace},
    {"split",     "Split s on each occurrence of separator into an array. Empty separator splits into characters.", op_split},
    {"join",      "Join an array of strings using separator.",                  op_join},
};
static const size_t NOPS = sizeof OPS / sizeof OPS[0];

/* Per-op property set: ordered property name list and a required flag. */
typedef struct { const char *name; int req; } propdef;
struct op_props_entry { op_fn fn; const propdef *props; size_t n; };
static const struct op_props_entry OP_PROPS[] = {
    { op_upper,     (const propdef[]){ {"s",1} },                                       1 },
    { op_lower,     (const propdef[]){ {"s",1} },                                       1 },
    { op_trim,      (const propdef[]){ {"s",1} },                                        1 },
    { op_length,    (const propdef[]){ {"s",1} },                                        1 },
    { op_reverse,   (const propdef[]){ {"s",1} },                                        1 },
    { op_substring, (const propdef[]){ {"s",1},{"start",1},{"length",0} },               3 },
    { op_contains,  (const propdef[]){ {"s",1},{"substring",1} },                       2 },
    { op_replace,   (const propdef[]){ {"s",1},{"old",1},{"new",1} },                    3 },
    { op_split,     (const propdef[]){ {"s",1},{"separator",1} },                        2 },
    { op_join,      (const propdef[]){ {"parts",1},{"separator",1} },                    2 },
};
static const propdef *op_props_for(const op_def *op, size_t *n) {
    for (size_t i = 0; i < sizeof OP_PROPS / sizeof OP_PROPS[0]; i++) {
        if (OP_PROPS[i].fn == op->fn) { *n = OP_PROPS[i].n; return OP_PROPS[i].props; }
    }
    fprintf(stderr, "schema: no property table for %s\n", op->name); exit(2);
}

/* Human-readable type name for a parameter name. */
static const char *prop_type_name(const char *pname) {
    if (strcmp(pname, "parts") == 0)              return "array of strings";
    if (strcmp(pname, "start") == 0 ||
        strcmp(pname, "length") == 0)            return "integer";
    return "string";
}

static jval schema_for(const op_def *op) {
    /* Each tool is {"type":"function","function":{"name":..,"description":..,"parameters":{...}}} */
    jval root = jval_new(J_OBJ); root.count = 1; root.items = calloc(2, sizeof(jval));
    jval tk = jval_new(J_STR); tk.str = strdup("type");
    jval tv = jval_new(J_STR); tv.str = strdup("function");
    root.items[0] = tk; root.items[1] = tv;

    /* function object appended as a second pair */
    jval fk = jval_new(J_STR); fk.str = strdup("function");
    jval fobj = jval_new(J_OBJ);
    /* name + description */
    fobj.count = 3; fobj.items = calloc(6, sizeof(jval));
    fobj.items[0] = (jval){J_STR, strdup("name"), 0, NULL, 0};
    fobj.items[1] = (jval){J_STR, strdup(op->name), 0, NULL, 0};
    fobj.items[2] = (jval){J_STR, strdup("description"), 0, NULL, 0};
    fobj.items[3] = (jval){J_STR, strdup(op->desc), 0, NULL, 0};
    fobj.items[4] = (jval){J_STR, strdup("parameters"), 0, NULL, 0};

    /* parameters: object schema with a per-op set of properties */
    jval params = jval_new(J_OBJ);
    jval props  = jval_new(J_OBJ);
    jval req    = jval_new(J_ARR);

    size_t np = 0;
    const propdef *pdef = op_props_for(op, &np);

    for (size_t i = 0; i < np; i++) {
        const char *pname = pdef[i].name;
        jval kk = jval_new(J_STR); kk.str = strdup(pname);
        jval sv;
        if (strcmp(pname, "parts") == 0) {
            sv = jval_new(J_OBJ); sv.count = 2; sv.items = calloc(4, sizeof(jval));
            sv.items[0] = (jval){J_STR, strdup("type"), 0, NULL, 0};
            sv.items[1] = (jval){J_STR, strdup("array"), 0, NULL, 0};
            sv.items[2] = (jval){J_STR, strdup("items"), 0, NULL, 0};
            jval its = jval_new(J_OBJ); its.count = 1; its.items = calloc(2, sizeof(jval));
            its.items[0] = (jval){J_STR, strdup("type"), 0, NULL, 0};
            its.items[1] = (jval){J_STR, strdup("string"), 0, NULL, 0};
            sv.items[3] = its;
        } else if (strcmp(pname, "start") == 0 || strcmp(pname, "length") == 0) {
            sv = jval_new(J_OBJ); sv.count = 1; sv.items = calloc(2, sizeof(jval));
            sv.items[0] = (jval){J_STR, strdup("type"), 0, NULL, 0};
            sv.items[1] = (jval){J_STR, strdup("integer"), 0, NULL, 0};
        } else {
            sv = jval_new(J_OBJ); sv.count = 1; sv.items = calloc(2, sizeof(jval));
            sv.items[0] = (jval){J_STR, strdup("type"), 0, NULL, 0};
            sv.items[1] = (jval){J_STR, strdup("string"), 0, NULL, 0};
        }
        props.items = realloc(props.items, (props.count + 1) * 2 * sizeof(jval));
        props.items[2 * props.count]     = kk;
        props.items[2 * props.count + 1] = sv;
        props.count++;
        if (pdef[i].req) {
            jval r = jval_new(J_STR); r.str = strdup(pname);
            req.items = realloc(req.items, (req.count + 1) * sizeof(jval));
            req.items[req.count++] = r;
        }
    }

    /* parameters object: type=object, properties, required */
    params.count = 3; params.items = calloc(6, sizeof(jval));
    params.items[0] = (jval){J_STR, strdup("type"), 0, NULL, 0};
    params.items[1] = (jval){J_STR, strdup("object"), 0, NULL, 0};
    params.items[2] = (jval){J_STR, strdup("properties"), 0, NULL, 0};
    params.items[3] = props;
    params.items[4] = (jval){J_STR, strdup("required"), 0, NULL, 0};
    params.items[5] = req;

    fobj.items[5] = params;
    root.items = realloc(root.items, (root.count + 1) * 2 * sizeof(jval));
    root.items[2 * root.count] = fk;
    root.items[2 * root.count + 1] = fobj;
    root.count++;
    return root;
}

static int emit_schema(void) {
    jval arr = jval_new(J_ARR); arr.items = calloc(NOPS, sizeof(jval));
    arr.count = NOPS;
    for (size_t i = 0; i < NOPS; i++) arr.items[i] = schema_for(&OPS[i]);
    sbuf out; sbuf_init(&out);
    jval_emit(&out, &arr);
    printf("%s\n", out.data ? out.data : "[]");
    sbuf_free(&out);
    jval_free(&arr);
    return 0;
}

static int emit_schema_human(void) {
    printf("stringtool: %lu operations\n", (unsigned long)NOPS);
    printf("(each operation is invoked as: stringtool <op> '<json-args>')\n\n");
    for (size_t i = 0; i < NOPS; i++) {
        const op_def *op = &OPS[i];
        printf("%lu. %s\n", (unsigned long)(i + 1), op->name);
        printf("    %s\n", op->desc);
        size_t np = 0;
        const propdef *pdef = op_props_for(op, &np);
        if (np) {
            printf("    arguments:\n");
            for (size_t j = 0; j < np; j++) {
                printf("      %-10s %s%s\n",
                       pdef[j].name, prop_type_name(pdef[j].name),
                       pdef[j].req ? "  (required)" : "  (optional)");
            }
        } else {
            printf("    arguments: (none)\n");
        }
        printf("    returns:   JSON object {\"result\": ...}\n");
        if (i + 1 < NOPS) printf("\n");
    }
    return 0;
}

/* ----- dispatch --------------------------------------------------------- */

static int dispatch(const char *opname, const char *jsonargs) {
    jval args = jparse(jsonargs);
    if (args.kind != J_OBJ) { fprintf(stderr, "args must be a JSON object\n"); exit(2); }
    for (size_t i = 0; i < NOPS; i++) {
        if (strcmp(OPS[i].name, opname) == 0) {
            jval r = OPS[i].fn(&args);
            sbuf out; sbuf_init(&out);
            jval_emit(&out, &r);
            printf("%s\n", out.data ? out.data : "{}");
            sbuf_free(&out);
            jval_free(&r);
            jval_free(&args);
            return 0;
        }
    }
    fprintf(stderr, "unknown operation: %s\n", opname);
    jval_free(&args);
    return 2;
}

static void usage(const char *prog) {
    fprintf(stderr,
        "usage: %s schema\n"
        "       %s schema-human\n"
        "       %s <op> '<json-args>'   (args may also be piped on stdin,\n"
        "                              or given as '-' to force stdin)\n"
        "\noperations:\n", prog, prog, prog);
    for (size_t i = 0; i < NOPS; i++) fprintf(stderr, "  %-10s %s\n", OPS[i].name, OPS[i].desc);
}

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
static void set_utf8_stdio(void) {
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
}
#else
static void set_utf8_stdio(void) {}
#endif

static char *read_all_stdin(void) {
    sbuf s; sbuf_init(&s);
    int c;
    while ((c = getchar()) != EOF) sbuf_putc(&s, (char)c);
    if (!s.data) s.data = strdup("");
    return s.data;
}

int main(int argc, char **argv) {
    set_utf8_stdio();
    if (getenv("STRINGTOOL_DEBUG")) {
        fprintf(stderr, "[debug] argc=%d\n", argc);
        for (int i = 0; i < argc; i++) fprintf(stderr, "[debug] argv[%d]=<%s>\n", i, argv[i]);
    }
    if (argc < 2) { usage(argv[0]); return 2; }
    if (strcmp(argv[1], "schema") == 0) {
        if (argc != 2) { usage(argv[0]); return 2; }
        return emit_schema();
    }
    if (strcmp(argv[1], "schema-human") == 0) {
        if (argc != 2) { usage(argv[0]); return 2; }
        return emit_schema_human();
    }
    /* Accept either:  stringtool <op> '<json>'   or   echo '<json>' | stringtool <op> -   */
    const char *opname = argv[1];
    const char *jsonargs;
    char *freed = NULL;
    if (argc == 3) {
        jsonargs = argv[2];
    } else if (argc == 2 && !isatty(0)) {
        jsonargs = freed = read_all_stdin();
    } else {
        usage(argv[0]); return 2;
    }
    if (strcmp(jsonargs, "-") == 0) { free(freed); jsonargs = freed = read_all_stdin(); }
    int rc = dispatch(opname, jsonargs);
    free(freed);
    return rc;
}