import json
import os
import pathlib

import pytest

from unstructured.cleaners.core import group_broken_paragraphs
from unstructured.documents.elements import Address, ListItem, NarrativeText, Title
from unstructured.partition.text import (
    combine_paragraphs_less_than_min,
    partition_text,
    split_content_to_fit_max,
)

DIRECTORY = pathlib.Path(__file__).parent.resolve()

EXPECTED_OUTPUT = [
    NarrativeText(text="This is a test document to use for unit tests."),
    Address(text="Doylestown, PA 18901"),
    Title(text="Important points:"),
    ListItem(text="Hamburgers are delicious"),
    ListItem(text="Dogs are the best"),
    ListItem(text="I love fuzzy blankets"),
]

MIN_MAX_TEXT = """This is a story. This is a story that doesn't matter
 because it is just being used as an example. Hi. Hello. Howdy. Hola.
 The example is simple and repetitive and long and somewhat boring,
 but it serves a purpose. End.""".replace(
    "\n",
    "",
)

SHORT_PARAGRAPHS = """This is a story.

This is a story that doesn't matter because it is just being used as an example.

Hi.

Hello.

Howdy.

Hola.

The example is simple and repetitive and long and somewhat boring, but it serves a purpose.

End.
"""


@pytest.mark.parametrize(
    ("filename", "encoding"),
    [
        ("fake-text.txt", "utf-8"),
        ("fake-text.txt", None),
        ("fake-text-utf-16-be.txt", "utf-16-be"),
    ],
)
def test_partition_text_from_filename(filename, encoding):
    filename_path = os.path.join(DIRECTORY, "..", "..", "example-docs", filename)
    elements = partition_text(filename=filename_path, encoding=encoding)
    assert len(elements) > 0
    assert elements == EXPECTED_OUTPUT
    for element in elements:
        assert element.metadata.filename == filename


def test_partition_text_from_filename_with_metadata_filename():
    filename_path = os.path.join(DIRECTORY, "..", "..", "example-docs", "fake-text.txt")
    elements = partition_text(
        filename=filename_path,
        encoding="utf-8",
        metadata_filename="test",
    )
    assert elements == EXPECTED_OUTPUT
    for element in elements:
        assert element.metadata.filename == "test"


@pytest.mark.parametrize(
    "filename",
    ["fake-text-utf-16.txt", "fake-text-utf-16-le.txt", "fake-text-utf-32.txt"],
)
def test_partition_text_from_filename_default_encoding(filename):
    filename_path = os.path.join(DIRECTORY, "..", "..", "example-docs", filename)
    elements = partition_text(filename=filename_path)
    assert len(elements) > 0
    assert elements == EXPECTED_OUTPUT
    for element in elements:
        assert element.metadata.filename == filename


@pytest.mark.parametrize(
    ("filename", "encoding", "error"),
    [
        ("fake-text.txt", "utf-16", UnicodeDecodeError),
        ("fake-text-utf-16-be.txt", "utf-16", UnicodeError),
    ],
)
def test_partition_text_from_filename_raises_econding_error(filename, encoding, error):
    with pytest.raises(error):
        filename = os.path.join(DIRECTORY, "..", "..", "example-docs", filename)
        partition_text(filename=filename, encoding=encoding)


def test_partition_text_from_file():
    filename = os.path.join(DIRECTORY, "..", "..", "example-docs", "fake-text.txt")
    with open(filename) as f:
        elements = partition_text(file=f)
    assert len(elements) > 0
    assert elements == EXPECTED_OUTPUT
    for element in elements:
        assert element.metadata.filename is None


def test_partition_text_from_file_with_metadata_filename():
    filename = os.path.join(DIRECTORY, "..", "..", "example-docs", "fake-text.txt")
    with open(filename) as f:
        elements = partition_text(file=f, metadata_filename="test")
    assert len(elements) > 0
    assert elements == EXPECTED_OUTPUT
    for element in elements:
        assert element.metadata.filename == "test"


@pytest.mark.parametrize(
    "filename",
    ["fake-text-utf-16.txt", "fake-text-utf-16-le.txt", "fake-text-utf-32.txt"],
)
def test_partition_text_from_file_default_encoding(filename):
    filename_path = os.path.join(DIRECTORY, "..", "..", "example-docs", filename)
    with open(filename_path) as f:
        elements = partition_text(file=f)
    assert len(elements) > 0
    assert elements == EXPECTED_OUTPUT
    for element in elements:
        assert element.metadata.filename is None


def test_partition_text_from_bytes_file():
    filename = os.path.join(DIRECTORY, "..", "..", "example-docs", "fake-text.txt")
    with open(filename, "rb") as f:
        elements = partition_text(file=f)
    assert len(elements) > 0
    assert elements == EXPECTED_OUTPUT
    for element in elements:
        assert element.metadata.filename is None


@pytest.mark.parametrize(
    "filename",
    ["fake-text-utf-16.txt", "fake-text-utf-16-le.txt", "fake-text-utf-32.txt"],
)
def test_partition_text_from_bytes_file_default_encoding(filename):
    filename_path = os.path.join(DIRECTORY, "..", "..", "example-docs", filename)
    with open(filename_path, "rb") as f:
        elements = partition_text(file=f)
    assert len(elements) > 0
    assert elements == EXPECTED_OUTPUT
    for element in elements:
        assert element.metadata.filename is None


def test_partition_text_from_text():
    filename = os.path.join(DIRECTORY, "..", "..", "example-docs", "fake-text.txt")
    with open(filename) as f:
        text = f.read()
    elements = partition_text(text=text)
    assert len(elements) > 0
    assert elements == EXPECTED_OUTPUT
    for element in elements:
        assert element.metadata.filename is None


def test_partition_text_from_text_works_with_empty_string():
    assert partition_text(text="") == []


def test_partition_text_raises_with_none_specified():
    with pytest.raises(ValueError):
        partition_text()


def test_partition_text_raises_with_too_many_specified():
    filename = os.path.join(DIRECTORY, "..", "..", "example-docs", "fake-text.txt")
    with open(filename) as f:
        text = f.read()

    with pytest.raises(ValueError):
        partition_text(filename=filename, text=text)


def test_partition_text_captures_everything_even_with_linebreaks():
    text = """
    VERY IMPORTANT MEMO
    DOYLESTOWN, PA 18901
    """
    elements = partition_text(text=text)
    assert elements == [
        Title(text="VERY IMPORTANT MEMO"),
        Address(text="DOYLESTOWN, PA 18901"),
    ]
    for element in elements:
        assert element.metadata.filename is None


def test_partition_text_groups_broken_paragraphs():
    text = """The big brown fox
was walking down the lane.

At the end of the lane,
the fox met a bear."""

    elements = partition_text(text=text, paragraph_grouper=group_broken_paragraphs)
    assert elements == [
        NarrativeText(text="The big brown fox was walking down the lane."),
        NarrativeText(text="At the end of the lane, the fox met a bear."),
    ]
    for element in elements:
        assert element.metadata.filename is None


def test_partition_text_extract_regex_metadata():
    text = "SPEAKER 1: It is my turn to speak now!"

    elements = partition_text(text=text, regex_metadata={"speaker": r"SPEAKER \d{1,3}"})
    assert elements[0].metadata.regex_metadata == {
        "speaker": [{"text": "SPEAKER 1", "start": 0, "end": 9}],
    }
    for element in elements:
        assert element.metadata.filename is None


def test_partition_text_splits_long_text(filename="example-docs/norwich-city.txt"):
    elements = partition_text(filename=filename)
    assert len(elements) > 0
    assert elements[0].text.startswith("Iwan Roberts")
    assert elements[-1].text.endswith("External links")


def test_partition_text_splits_long_text_max_partition(filename="example-docs/norwich-city.txt"):
    elements = partition_text(filename=filename)
    elements_max_part = partition_text(filename=filename, max_partition=500)
    # NOTE(klaijan) - I edited the operation here from < to <=
    # Please revert back if this does not make sense
    assert len(elements) <= len(elements_max_part)
    for element in elements_max_part:
        assert len(element.text) <= 500

    # Make sure combined text is all the same
    assert " ".join([el.text for el in elements]) == " ".join([el.text for el in elements_max_part])


def test_partition_text_splits_max_min_partition(filename="example-docs/norwich-city.txt"):
    elements = partition_text(filename=filename)
    elements_max_part = partition_text(filename=filename, min_partition=1000, max_partition=1500)
    for i, element in enumerate(elements_max_part):
        # NOTE(robinson) - the last element does not have a next element to merge with,
        # so it can be short
        if i < len(elements_max_part) - 1:
            assert len(element.text) <= 1500
            assert len(element.text) >= 1000

    import re

    from unstructured.nlp.patterns import BULLETS_PATTERN

    # NOTE(klaijan) - clean the asterik out of both text.
    # The `elements` was partitioned by new line and thus makes line 56 (shown below)
    # "*Club domestic league appearances and goals"
    # be considered as a bullet point by the function is_bulleted_text
    # and so the asterik was removed from the paragraph
    # whereas `elements_max_part` was partitioned differently and thus none of the line
    # starts with any of the BULLETS_PATTERN.

    # TODO(klaijan) - when edit the function partition_text to support non-bullet paragraph
    # that starts with bullet-like BULLETS_PATTERN, remove the re.sub part from the assert below.

    # Make sure combined text is all the same
    assert re.sub(BULLETS_PATTERN, "", " ".join([el.text for el in elements])) == re.sub(
        BULLETS_PATTERN,
        "",
        " ".join([el.text for el in elements_max_part]),
    )


def test_partition_text_min_max(filename="example-docs/norwich-city.txt"):
    segments = partition_text(
        text=SHORT_PARAGRAPHS,
        min_partition=6,
    )
    for i, segment in enumerate(segments):
        # NOTE(robinson) - the last element does not have a next element to merge with,
        # so it can be short
        if i < len(segments) - 1:
            assert len(segment.text) >= 6

    segments = partition_text(
        text=SHORT_PARAGRAPHS,
        max_partition=20,
        min_partition=7,
    )
    for i, segment in enumerate(segments):
        # NOTE(robinson) - the last element does not have a next element to merge with,
        # so it can be short
        if i < len(segments) - 1:
            assert len(segment.text) >= 7
            assert len(segment.text) <= 20


def test_split_content_to_fit_max():
    segments = split_content_to_fit_max(
        content=MIN_MAX_TEXT,
        max_partition=75,
    )
    assert segments == [
        "This is a story.",
        "This is a story that doesn't matter because",
        "it is just being used as an example. Hi. Hello. Howdy. Hola.",
        "The example is simple and repetitive and long",
        "and somewhat boring, but it serves a purpose. End.",
    ]


def test_combine_paragraphs_less_than_min():
    segments = combine_paragraphs_less_than_min(
        SHORT_PARAGRAPHS.split("\n\n"),
        max_partition=1500,
        min_partition=7,
    )
    assert len(segments) < len(SHORT_PARAGRAPHS)


def test_partition_text_doesnt_get_page_breaks():
    text = "--------------------"
    elements = partition_text(text=text)
    assert len(elements) == 1
    assert elements[0].text == text
    assert not isinstance(elements[0], ListItem)


@pytest.mark.parametrize(
    ("filename", "encoding"),
    [
        ("fake-text.txt", "utf-8"),
        ("fake-text.txt", None),
        ("fake-text-utf-16-be.txt", "utf-16-be"),
    ],
)
def test_partition_text_from_filename_exclude_metadata(filename, encoding):
    filename = os.path.join(DIRECTORY, "..", "..", "example-docs", filename)
    elements = partition_text(
        filename=filename,
        encoding=encoding,
        include_metadata=False,
    )
    for i in range(len(elements)):
        assert elements[i].metadata.to_dict() == {}


def test_partition_text_from_file_exclude_metadata():
    filename = os.path.join(DIRECTORY, "..", "..", "example-docs", "fake-text.txt")
    with open(filename) as f:
        elements = partition_text(file=f, include_metadata=False)
    for i in range(len(elements)):
        assert elements[i].metadata.to_dict() == {}


def test_partition_text_metadata_date(
    mocker,
    filename="example-docs/fake-text.txt",
):
    mocked_last_modification_date = "2029-07-05T09:24:28"

    mocker.patch(
        "unstructured.partition.text.get_last_modified_date",
        return_value=mocked_last_modification_date,
    )

    elements = partition_text(
        filename=filename,
    )

    assert elements[0].metadata.last_modified == mocked_last_modification_date


def test_partition_text_with_custom_metadata_date(
    mocker,
    filename="example-docs/fake-text.txt",
):
    mocked_last_modification_date = "2029-07-05T09:24:28"
    expected_last_modification_date = "2020-07-05T09:24:28"

    mocker.patch(
        "unstructured.partition.text.get_last_modified_date",
        return_value=mocked_last_modification_date,
    )

    elements = partition_text(
        filename=filename,
        metadata_last_modified=expected_last_modification_date,
    )

    assert elements[0].metadata.last_modified == expected_last_modification_date


def test_partition_text_from_file_metadata_date(
    mocker,
    filename="example-docs/fake-text.txt",
):
    mocked_last_modification_date = "2029-07-05T09:24:28"

    mocker.patch(
        "unstructured.partition.text.get_last_modified_date_from_file",
        return_value=mocked_last_modification_date,
    )

    with open(filename, "rb") as f:
        elements = partition_text(
            file=f,
        )

    assert elements[0].metadata.last_modified == mocked_last_modification_date


def test_partition_text_from_file_with_custom_metadata_date(
    mocker,
    filename="example-docs/fake-text.txt",
):
    mocked_last_modification_date = "2029-07-05T09:24:28"
    expected_last_modification_date = "2020-07-05T09:24:28"

    mocker.patch(
        "unstructured.partition.text.get_last_modified_date_from_file",
        return_value=mocked_last_modification_date,
    )

    with open(filename, "rb") as f:
        elements = partition_text(file=f, metadata_last_modified=expected_last_modification_date)

    assert elements[0].metadata.last_modified == expected_last_modification_date


def test_partition_text_from_text_metadata_date(
    filename="example-docs/fake-text.txt",
):
    with open(filename) as f:
        text = f.read()

    elements = partition_text(
        text=text,
    )
    assert elements[0].metadata.last_modified is None


def test_partition_text_from_text_with_custom_metadata_date(
    filename="example-docs/fake-text.txt",
):
    expected_last_modification_date = "2020-07-05T09:24:28"

    with open(filename) as f:
        text = f.read()

    elements = partition_text(text=text, metadata_last_modified=expected_last_modification_date)

    assert elements[0].metadata.last_modified == expected_last_modification_date


def test_partition_text_with_unique_ids():
    elements = partition_text(text="hello there!")
    assert elements[0].id == "c69509590d81db2f37f9d75480c8efed"
    # Test that the element is JSON serializable. This should run without an error
    json.dumps(elements[0].to_dict())

    elements = partition_text(text="hello there!", unique_element_ids=True)
    assert len(elements[0].id) == 36
    assert elements[0].id.count("-") == 4
    # Test that the element is JSON serializable. This should run without an error
    json.dumps(elements[0].to_dict())
