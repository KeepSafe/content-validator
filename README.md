content-validator
=================

Content validator looks at text content and preforms different validation tasks.

## Requirements

1. Python 2.7.+

## Installation

`make install`

## Usage

Generally it's easiest to write a separate test for each validation case. The simplest example:

```
f = files('src/**/*.txt')
parser = create_parser(Filetype.txt)
reporter = ConsoleReporter()
check = urls_txt()
v = Validator(checks=[check], files=f, parser=parser, reporter=reporter)
self.assertEqual({}, v.validate())
```

### Files

The `files` function takes a pattern and resolves it to file paths. You can pass any glob like pattern but in addition you can include the parameters. The parameter is used when you want to compare content. Let's say you have translations in English and German. You have two files `src/en/myfile.txt`  and `src/de/myfile.txt` for English and German. The pattern might look something like this `src/{lang}/myfile.txt`. In addition you need to say which file will be the base of the comparison, in case you have more then 2 files. To do that you need to pass all parameters you are using in the pattern as named parameters for the `files` call. Finally the call should look something like this:

`files('src/{lang}/*.txt', lang='en')`

In case you are not doing any comparison checks you can use a usual glob like pattern `files('src/**/*.txt')`

### Parsers

When the file is first read it the data you want to validate needs to be extracted from it. The simplest example is a text file. Nothing is done here except reading the file content. The more complex example is when, for eg., you have embedded markdown in an xml tag. To extract the data you should create a chain of parsers. First you want to extract all tags from the xml. Second you want to parse the content of the tags from markdown to html. Here is an example how to do that:

`chain_parsers([Filetype.xml, Filetype.md], query='//strings')`

The xml parser takes additional parameter `query` used to extract the tags. You can pass it to `create_parser` in the same way:

`create_parser(Filetype.xml, query='//strings')`

Available parsers types:

* `Filetype.txt` - simply reads the file
* `Filetype.md` - converts markdown to 
* `Filetype.xml` - extracts text from xml and concatenates
* `Filetype.csv` - puts every value on a separate line

### Reporters

Shows the result of the validation. There are 2 reporters available:

* `HtmlReporter` - creates an error file for every error
* `ConsoleReporter` - print the error to the console

### Checks

Checks perform validation on the content. Wether it's url or structure or anything else. If the content in not valid the check will return an error which later can be passed to a reporter.

Available checks:

* `urls_txt()` - validates if the url is accessible in a text file
* `urls_html(root_url='', skip_images=False)` - same as text but extracts links from `<a>` and `<img>`. You can provide root for relative urls and skip `<img>` if needed
* `markdown()` - validates markdown structure by comparing it with the base

## Example

A more detailed example looks like this:

```
class TestEmail(TestCase):

    def test_email(self):
        f = files('src/{lang}/*.xml', lang='en')
        parser = create_parser(Filetype.xml, query='.//string')
        reporter = HtmlReporter()
        md = markdown()
        v = Validator(checks=[md], files=f, parser=parser, reporter=reporter)
        self.assertEqual({}, v.validate())

    def test_urls(self):
        f = files('src/{lang}/*.xml', lang='en')
        parser = chain_parsers([Filetype.xml, Filetype.md], query='.//string')
        reporter = ConsoleReporter()
        urls = urls_html(skip_images=True)
        v = Validator(checks=[urls], files=f, parser=parser, reporter=reporter)
        self.assertEqual({}, v.validate())

    def test_in_html_output(self):
        f = files('target/{lang}/*.html', lang='en')
        parser = create_parser(Filetype.txt)
        reporter = ConsoleReporter()
        urls = urls_html()
        v = Validator(checks=[urls], files=f, parser=parser, reporter=reporter)
        self.assertEqual({}, v.validate())

    def test_in_txt_output(self):
        f = files('target/{lang}/*.text', lang='en')
        parser = create_parser(Filetype.txt)
        reporter = ConsoleReporter()
        urls = urls_txt()
        v = Validator(checks=[urls], files=f, parser=parser, reporter=reporter)
        self.assertEqual({}, v.validate())
```