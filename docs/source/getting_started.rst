Getting Started
===============

The following section will cover basic concepts and usage patterns in ``unstructured``.
After reading this section, you should be able to:

* Partitioning a document with the ``partition`` function.
* Understand how documents are structured in ``unstructured``.
* Convert a document to a dictionary and/or save it as a JSON.

The example documents in this section come from the
`example-docs <https://github.com/Unstructured-IO/unstructured/tree/main/example-docs>`_
directory in the ``unstructured`` repo.

Before running the code in this make sure you've installed the ``unstructured`` library
and all dependencies using the instructions in the **Quick Start** section.


#######################
Partitioning a document
#######################

In this section, we'll cut right to the chase and get to the most important part of the library: partitioning a document.
The goal of document partitioning is to read in a source document, split the document into sections, categorize those sections,
and extract the text associated with those sections. Depending on the document type, unstructured uses different methods for
partitioning a document. We'll cover those in a later section. For now, we'll use the simplest API in the library,
the ``partition`` function. The ``partition`` function will detect the filetype of the source document and route it to the appropriate
partitioning function. You can try out the partition function by running the cell below.


.. code:: python


	from unstructured.partition.auto import partition

	elements = partition(filename="example-10k.html")


You can also pass in a file as a file-like object using the following workflow:


.. code:: python

	with open("example-10k.html", "rb") as f:
	    elements = partition(file=f)


The ``partition`` function uses `libmagic <https://formulae.brew.sh/formula/libmagic>`_ for filetype detection. If ``libmagic`` is
not present and the user passes a filename, ``partition`` falls back to detecting the filetype using the file extension.
``libmagic`` is required if you'd like to pass a file-like object to ``partition``.
We highly recommend installing ``libmagic`` and you may observe different file detection behaviors
if ``libmagic`` is not installed`.


##################
Document elements
##################


When we partition a document, the output is a list of document ``Element`` objects.
These element objects represent different components of the source document. Currently, the ``unstructured`` library supports the following element types:



* ``Element``
	* ``Text``
		* ``FigureCaption``
		* ``NarrativeText``
		* ``ListItem``
		* ``Title``
		* ``Address``
		* ``Table``
		* ``PageBreak``
		* ``Header``
		* ``Footer``
        	* ``EmailAddress``
	* ``CheckBox``
	* ``Image``


Other element types that we will add in the future include tables and figures.
Different partitioning functions use different methods for determining the element type and extracting the associated content.
Document elements have a ``str`` representation. You can print them using the snippet below.


.. code:: python

	elements = partition(filename="example-10k.html")

	for element in elements[:5]:
	    print(element)
	    print("\n")


One helpful aspect of document elements is that they allow you to cut a document down to the elements that you need for your particular use case.
For example, if you're training a summarization model you may only want to include narrative text for model training.
You'll notice that the output above includes a lot of titles and other content that may not be suitable for a summarization model.
The following code shows how you can limit your output to only narrative text with at least two sentences. As you can see, the output now only contains narrative text.



.. code:: python

	from unstructured.documents.elements import NarrativeText
	from unstructured.partition.text_type import sentence_count

	for element in elements[:100]:
	    if isinstance(element, NarrativeText) and sentence_count(element.text) > 2:
	        print(element)
	        print("\n")


######
Tables
######

For ``Table`` elements, the raw text of the table will be stored in the ``text`` attribute for the Element, and HTML representation
of the table will be available in the element metadata under ``element.metadata.text_as_html``. For most documents where
table extraction is available, the ``partition`` function will extract tables automatically if they are present.
For PDFs and images, table extraction requires a relatively expensive call to a table recognition model, and so for those
document types table extraction is an option you need to enable. If you would like to extract tables for PDFs or images,
pass in ``infer_table_structured=True``. Here is an example:

.. code:: python

    from unstructured.partition.pdf import partition_pdf

    filename = "example-docs/layout-parser-paper.pdf"

    elements = partition_pdf(filename=filename, infer_table_structure=True)
    tables = [el for el in elements if el.category == "Table"]

    print(tables[0].text)
    print(tables[0].metadata.text_as_html)

The text will look like this:


.. code:: python

	Dataset Base Model1 Large Model Notes PubLayNet [38] F / M M Layouts of modern scientific documents PRImA [3] M - Layouts of scanned modern magazines and scientific reports Newspaper [17] F - Layouts of scanned US newspapers from the 20th century TableBank [18] F F Table region on modern scientific and business document HJDataset [31] F / M - Layouts of history Japanese documents


And the ``text_as_html`` metadata will look like this:

.. code:: html

	<table><thead><th>Dataset</th><th>| Base Model’</th><th>| Notes</th></thead><tr><td>PubLayNet</td><td>[38] F/M</td><td>Layouts of modern scientific documents</td></tr><tr><td>PRImA [3]</td><td>M</td><td>Layouts of scanned modern magazines and scientific reports</td></tr><tr><td>Newspaper</td><td>F</td><td>Layouts of scanned US newspapers from the 20th century</td></tr><tr><td>TableBank</td><td>F</td><td>Table region on modern scientific and business document</td></tr><tr><td>HJDataset [31]</td><td>F/M</td><td>Layouts of history Japanese documents</td></tr></table>

####################
Serializing Elements
####################

The ``unstructured`` library includes helper functions for
reading and writing a list of ``Element`` objects to and
from JSON. You can use the following workflow for
serializing and deserializing an ``Element`` list.


.. code:: python

    from unstructured.documents.elements import ElementMetadata, Text, Title, FigureCaption
    from unstructured.staging.base import elements_to_json, elements_from_json

    filename = "my-elements.json"
    metadata = ElementMetadata(filename="fake-file.txt")
    elements = [
        FigureCaption(text="caption", metadata=metadata, element_id="1"),
        Title(text="title", metadata=metadata, element_id="2"),
        Text(text="title", metadata=metadata, element_id="3"),

    ]

    elements_to_json(elements, filename=filename)
    new_elements = elements_from_json(filename=filename)

    # alternatively, one can also serialize/deserialize to/from a string with:
    serialized_elements_json = elements_to_json(elements)
    new_elements = elements_from_json(text=serialized_elements_json)

###########################################
Converting elements to a dictionary or JSON
###########################################

The final step in the process for most users is to convert the output to JSON.
You can convert a list of document elements to a list of dictionaries using the ``convert_to_dict`` function.
The workflow for using ``convert_to_dict`` appears below.


.. code:: python


	from unstructured.staging.base import convert_to_dict

	convert_to_dict(elements)


The ``unstructured`` library also includes utilities for saving a list of elements to JSON and reading
a list of elements from JSON, as seen in the snippet below



.. code:: python

    from unstructured.staging.base import elements_to_json, elements_from_json


    filename = "outputs.json"
    elements_to_json(elements, filename=filename)
    elements = elements_from_json(filename=filename)


###################
Unique Element IDs
###################

By default, the element ID is a SHA-256 hash of the element text. This is to ensure that
the ID is deterministic. One downside is that the ID is not guaranteed to be unique.
Different elements with the same text will have the same ID, and there could also
be hash collisions. To use UUIDs in the output instead, you can pass
``unique_element_ids=True`` into any of the partition functions. This can be helpful
if you'd like to use the IDs as a primary key in a database, for example.

.. code:: python

    from unstructured.partition.text import partition_text

    elements = partition_text(text="Here is some example text.", unique_element_ids=True)
    elements[0].id


##################
Wrapping it all up
##################

To conclude, the basic workflow for reading in a document and converting it to a JSON in ``unstructured``
looks like the following:



.. code:: python

    from unstructured.partition.auto import partition
    from unstructured.staging.base import elements_to_json

    input_filename = "example-10k.html"
    output_filename = "outputs.json"

    elements = partition(filename=input_filename)
    elements_to_json(elements, filename=output_filename)
