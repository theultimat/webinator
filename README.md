# Webinator

Extremely simple static site generator that converts Markdown into HTML borne
out of dependency hell frustration. This project assumes you have the following
installed and are running from something somewhat like a `bash` shell:

- `python` >= 3.8 (including `pip`)
- `make`
- `find`

Webinator automatically sets up a python virtual environment and will install
the following package(s) using `pip`:

- `markdown==3.9`

## Usage

Webinator is designed to be cloned as a subdirectory of a website's source
repository and relies on `make` to handle dependencies. Webinator's Makefile
should be included in the source repository's Makefile after defining the
following variables:

- `HTML_SRC_DIR` sets the root directory that contains the Markdown files to
  be converted to HTML.
- `HTML_TEMPLATE` is the path to the template file to use.
- `HTML_DEPS` is optional and specifies any extra dependencies for the input
  files that should result in a rebuild (e.g. include files).
- `STATIC_DIR` is optional and specifies the root of any static content that
  should be copied directly into the output site directory (e.g. CSS).

For example, if we have the following files in the root directory alongside
the webinator directory

    .
    ├── inc.html
    ├── Makefile
    ├── src
    │   └── test.md
    ├── static
    │   └── css
    │       └── test.css
    └── template.html

And set up our Makefile as

```Makefile
HTML_SRC_DIR  := src
HTML_TEMPLATE := template.html
HTML_DEPS     := inc.html
STATIC_DIR    := static

include webinator/Makefile
```

Then running `make` will generate the following output

    .
    └── build
        ├── site
        │   ├── css
        │   │   └── test.css
        │   └── test.html
        └── venv

The `site` directory is the final static site and can be copied to the desired
location.

## Markdown Syntax

Webinator assumes the input Markdown files start with a list of attribute lines
of the form `@key: value`. Keys must be all lowercase and can only contain valid
identifier characters i.e. `[a-z_0-9]`.

As soon as webinator encounters a line that is not an attribute it will assume
the main body of the Markdown file has started and convert the rest of the file
into HTML.

## Template Syntax

The templating system of webinator is extremely simple and only supports a few
features:

### Attribute Substitution

Values of attributes can be inserted using `$${key}`. For example, if in the
Markdown file we have

    @name: world

And the template consists of

```html
<h1>Hello $${name}!</h1>
```

Webniator will generate the output

```html
<h1>Hello world!</h1>
```

### Conditional Evaluation

Webinator can handle extremely simple conditions based on whether an attribute
evaluates to true or false. Supported conditions are `$$if` and `$$ifn` (if
not). All conditions must be tagged so webinator can easily find the
corresponding `end` that denotes the end of the conditional block. Tags must be
unique and follow immediately after the condition and a colon.

- `$$if:tag{attrib} ... $$end:tag{}`
- `$$ifn:tag{attrib} ... $$end:tag{}`

Assuming we have the same `name` attribute from the previous example, if we have
the template

```html
$$if:x{name}
<p>name exists!</p>
$$end:x{}
$$ifn:y{name}
<p>name does not exist!</p>
$$end:y{}
```

Webinator will generate the output

```html
<p>name exists!</p>
```

### Includes

Other files can be included using `$$inc{path}`. This works similary to the C
preprocessor in that it just replaces the include tag with the contents of the
file at `path`.

Includes are evaluated after conditionals allowing for files to be conditionally
included. Conditional and include substitutions are applied recursively until
no more matching values are found.
