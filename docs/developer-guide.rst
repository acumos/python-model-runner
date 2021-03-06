.. ===============LICENSE_START=======================================================
.. Acumos CC-BY-4.0
.. ===================================================================================
.. Copyright (C) 2017-2018 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
.. ===================================================================================
.. This Acumos documentation file is distributed by AT&T and Tech Mahindra
.. under the Creative Commons Attribution 4.0 International License (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..      http://creativecommons.org/licenses/by/4.0
..
.. This file is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
.. ===============LICENSE_END=========================================================

==========================================
Acumos Python Model Runner Developer Guide
==========================================

Testing
=======

We use a combination of ``tox``, ``pytest``, and ``flake8`` to test
``acumos_model_runner``. Code which is not PEP8 compliant (aside from E501) will be
considered a failing test. You can use tools like ``autopep8`` to
“clean” your code as follows:

.. code:: bash

    $ pip install autopep8
    $ cd python-model-runner
    $ autopep8 -r --in-place --ignore E501 acumos_model_runner/ testing/ examples/

Run tox directly:

.. code:: bash

    $ cd python-model-runner
    $ tox

You can also specify certain tox environments to test:

.. code:: bash

    $ tox -e py34  # only test against Python 3.4
    $ tox -e flake8  # only lint code

And finally, you can run pytest directly in your environment *(recommended starting place)*:

.. code:: bash

    $ pytest
    $ pytest -s   # verbose output
