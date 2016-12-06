# -*- coding: utf-8 -*-
"""

    eater.tests.api.http
    ~~~~~~~~~~~~~~~~~~~~

    Tests on :py:mod:`eater.api.http`
"""

import pytest
from requests.structures import CaseInsensitiveDict
import requests_mock
from schematics import Model
from schematics.exceptions import DataError
from schematics.types import StringType

from eater import HTTPEater


def test_can_subclass():
    class PersonAPI(HTTPEater):
        request_cls = Model
        response_cls = Model
        url = 'http://example.com'
    PersonAPI()


def test_request_cls_defaults_none():
    class PersonAPI(HTTPEater):  # pylint: disable=abstract-method
        response_cls = Model
        url = 'http://example.com'

    api = PersonAPI()
    assert api.request_cls is None


def test_get_url_with_request_cls_none():  # pylint: disable=invalid-name
    class PersonAPI(HTTPEater):  # pylint: disable=abstract-method
        response_cls = Model
        url = 'http://example.com'

    api = PersonAPI(None)
    assert api.url == 'http://example.com'


def test_must_define_response_cls():
    class PersonAPI(HTTPEater):  # pylint: disable=abstract-method
        request_cls = Model
        url = 'http://example.com'

    with pytest.raises(TypeError):
        PersonAPI()  # pylint: disable=abstract-class-instantiated


def test_must_define_url():
    class PersonAPI(HTTPEater):  # pylint: disable=abstract-method
        request_cls = Model
        response_cls = Model

    with pytest.raises(TypeError):
        PersonAPI()  # pylint: disable=abstract-class-instantiated


def test_get_request():
    class Person(Model):
        name = StringType()

    class PersonAPI(HTTPEater):
        request_cls = Person
        response_cls = Person
        url = 'http://example.com/person'

    expected_person = Person(dict(name='John'))
    api = PersonAPI(name=expected_person.name)

    with requests_mock.Mocker() as mock:
        mock.get(
            api.url,
            json=expected_person.to_primitive(),
            headers=CaseInsensitiveDict({
                'Content-Type': 'application/json'
            })
        )

        actual_person = api()
        assert actual_person == expected_person

        # Now check that api can take a model as the first parameter
        api = PersonAPI(expected_person)
        actual_person = api()
        assert actual_person == expected_person


def test_request_cls_none():
    class Person(Model):
        name = StringType()

    class PersonAPI(HTTPEater):
        request_cls = None
        response_cls = Person
        url = 'http://example.com/person'

    expected_person = Person(dict(name='John'))
    api = PersonAPI(name=expected_person.name)

    with requests_mock.Mocker() as mock:
        mock.get(
            api.url,
            json=expected_person.to_primitive(),
            headers=CaseInsensitiveDict({
                'Content-Type': 'application/json'
            })
        )

        actual_person = api()
        assert actual_person == expected_person


def test_data_error_raised():
    class Person(Model):
        name = StringType(required=True, min_length=4)

    class PersonAPI(HTTPEater):
        request_cls = Person
        response_cls = Person
        url = 'http://example.com/person'

    api = PersonAPI(name='John')

    with pytest.raises(DataError):
        with requests_mock.Mocker() as mock:
            mock.get(
                api.url,
                json={'name': 'Joh'},
                headers=CaseInsensitiveDict({
                    'Content-Type': 'application/json'
                })
            )
            api()


def test_url_formatting():
    class Person(Model):
        name = StringType()

    class GetPersonAPI(HTTPEater):
        request_cls = Person
        response_cls = Person
        url = 'http://example.com/person/{request_model.name}/'

    expected_url = 'http://example.com/person/John/'

    api = GetPersonAPI(name='John')
    assert api.url == expected_url

    with requests_mock.Mocker() as mock:
        mock.get(
            expected_url,
            json={'name': 'John'},
            headers=CaseInsensitiveDict({
                'Content-Type': 'application/json'
            })
        )
        response = api()
        assert response.name == 'John'


def test_get_url():
    class Person(Model):
        name = StringType()

    class GetPersonAPI(HTTPEater):
        request_cls = Person
        response_cls = Person
        url = 'http://example.com/person/'

        def get_url(self) -> str:
            return '%s%s/' % (type(self).url, self.request_model.name)

    expected_url = 'http://example.com/person/John/'

    api = GetPersonAPI(name='John')
    assert api.url == expected_url

    with requests_mock.Mocker() as mock:
        mock.get(
            'http://example.com/person/John/',
            json={'name': 'John'},
            headers=CaseInsensitiveDict({
                'Content-Type': 'application/json'
            })
        )
        response = api()
        assert response.name == 'John'
